import socket
from unittest.mock import MagicMock

import pytest

from tasks.scrapers import utils


def _addrinfo(ip: str):
    return [(socket.AF_INET, socket.SOCK_STREAM, 6, "", (ip, 80))]


@pytest.mark.parametrize(
    "ip", ["127.0.0.1", "10.0.0.5", "172.18.0.2", "192.168.1.1", "169.254.169.254"]
)
def test_non_public_addresses_are_blocked(monkeypatch, ip) -> None:
    monkeypatch.setattr(utils.socket, "getaddrinfo", lambda *a, **k: _addrinfo(ip))
    assert utils.is_public_url("http://example.com/") is False


def test_public_address_is_allowed(monkeypatch) -> None:
    monkeypatch.setattr(utils.socket, "getaddrinfo", lambda *a, **k: _addrinfo("93.184.216.34"))
    assert utils.is_public_url("https://example.com/") is True


def test_unresolvable_host_and_bad_scheme_are_blocked(monkeypatch) -> None:
    def boom(*a, **k):
        raise socket.gaierror

    monkeypatch.setattr(utils.socket, "getaddrinfo", boom)
    assert utils.is_public_url("http://nope.invalid/") is False
    assert utils.is_public_url("file:///etc/passwd") is False
    assert utils.is_public_url("ftp://example.com/") is False


def test_get_refuses_private_target_without_any_request(monkeypatch) -> None:
    monkeypatch.setattr(utils.socket, "getaddrinfo", lambda *a, **k: _addrinfo("127.0.0.1"))
    requested = MagicMock()
    monkeypatch.setattr(utils.requests, "get", requested)
    assert utils.get("http://localhost:6379/") is None
    requested.assert_not_called()


def test_get_blocks_redirect_to_private_address(monkeypatch) -> None:
    def fake_getaddrinfo(host, *a, **k):
        return _addrinfo("93.184.216.34" if host == "public.example" else "10.0.0.7")

    redirect = MagicMock(status_code=302, headers={"Location": "http://internal.example/admin"})
    monkeypatch.setattr(utils.socket, "getaddrinfo", fake_getaddrinfo)
    monkeypatch.setattr(utils, "robots_allowed", lambda *a, **k: True)
    calls = []

    def fake_get(url, **kw):
        calls.append(url)
        return redirect

    monkeypatch.setattr(utils.requests, "get", fake_get)
    assert utils.get("http://public.example/start") is None
    assert calls == ["http://public.example/start"]  # internal host never contacted


def test_get_caps_response_size(monkeypatch) -> None:
    monkeypatch.setattr(utils.socket, "getaddrinfo", lambda *a, **k: _addrinfo("93.184.216.34"))
    monkeypatch.setattr(utils, "robots_allowed", lambda *a, **k: True)
    big = MagicMock(status_code=200, headers={})
    big.iter_content.return_value = iter([b"x" * 1024 * 1024] * 50)  # would be 50 MB
    monkeypatch.setattr(utils.requests, "get", lambda *a, **k: big)
    resp = utils.get("http://public.example/")
    assert resp is not None
    assert len(resp.content) <= utils.MAX_RESPONSE_BYTES + 1024 * 1024


def test_robots_disallow_is_respected(monkeypatch) -> None:
    robots = MagicMock(status_code=200, text="User-agent: *\nDisallow: /private\n")
    monkeypatch.setattr(utils.requests, "get", lambda *a, **k: robots)
    assert utils.robots_allowed("http://site.example/private/page") is False
    assert utils.robots_allowed("http://site.example/public") is True


def test_robots_unreachable_fails_open(monkeypatch) -> None:
    def boom(*a, **k):
        raise utils.requests.ConnectionError

    monkeypatch.setattr(utils.requests, "get", boom)
    assert utils.robots_allowed("http://site.example/anything") is True
