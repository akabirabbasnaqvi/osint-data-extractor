from typing import Optional

import pytest
from fastapi import Depends, FastAPI
from fastapi.testclient import TestClient

from session import optional_session_id

app = FastAPI()


@app.get("/whoami")
def whoami(session_id: Optional[str] = Depends(optional_session_id)):
    return {"session_id": session_id}


client = TestClient(app)


def test_missing_header_means_no_session() -> None:
    assert client.get("/whoami").json() == {"session_id": None}


def test_valid_session_id_is_passed_through() -> None:
    res = client.get("/whoami", headers={"X-Session-ID": "abc12345-def"})
    assert res.json() == {"session_id": "abc12345-def"}


@pytest.mark.parametrize("bad", ["short", "has spaces in it!", "x" * 65, "semi;colon-1234"])
def test_malformed_session_id_is_rejected(bad: str) -> None:
    assert client.get("/whoami", headers={"X-Session-ID": bad}).status_code == 400
