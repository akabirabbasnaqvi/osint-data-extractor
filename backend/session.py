"""
Anonymous per-browser session identity.

The app has no accounts, so each browser generates a random id and sends it
in the `X-Session-ID` header. Jobs are stamped with it so the history list
and delete endpoints only ever expose a visitor's own searches -- without
this, anybody could list (and delete) every other visitor's searches,
including the personal details they typed in.
"""
import re
from typing import Optional

from fastapi import Header, HTTPException

SESSION_ID_PATTERN = re.compile(r"^[A-Za-z0-9_-]{8,64}$")


def optional_session_id(x_session_id: Optional[str] = Header(default=None)) -> Optional[str]:
    if x_session_id is None:
        return None
    if not SESSION_ID_PATTERN.fullmatch(x_session_id):
        raise HTTPException(status_code=400, detail="Invalid X-Session-ID header")
    return x_session_id
