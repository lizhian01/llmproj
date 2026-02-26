import os
from typing import Optional

from fastapi import Header, HTTPException

from server.services.auth import decode_access_token
from server.services.user_store import get_user_by_id


def _allow_guest() -> bool:
    return os.getenv("AUTH_ALLOW_GUEST", "false").lower() in {"1", "true", "yes"}


def _get_token_from_header(authorization: Optional[str]) -> Optional[str]:
    if not authorization:
        return None
    if not authorization.lower().startswith("bearer "):
        raise HTTPException(status_code=401, detail="Invalid authorization header")
    return authorization.split(" ", 1)[1].strip()


def get_current_user(authorization: Optional[str] = Header(None)) -> dict:
    token = _get_token_from_header(authorization)
    if not token:
        if _allow_guest():
            return {"id": "guest", "username": "guest", "created_at": None, "is_guest": True}
        raise HTTPException(status_code=401, detail="Not authenticated")

    payload = decode_access_token(token)
    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(status_code=401, detail="Invalid token")

    user = get_user_by_id(user_id)
    if not user or user.get("deleted_at"):
        raise HTTPException(status_code=401, detail="Invalid token")
    return {"id": user["id"], "username": user["username"], "created_at": user["created_at"]}
