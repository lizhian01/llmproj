from typing import Optional

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field

from server.api.deps import get_current_user
from server.services.auth import create_access_token, hash_password, verify_password
from server.services.kb_store import delete_user_kb_files
from server.services.user_store import create_user, delete_user, get_user_by_id, get_user_by_username


router = APIRouter(prefix="/api/auth", tags=["auth"])


class AuthRequest(BaseModel):
    username: str = Field(..., min_length=3, max_length=32)
    password: str = Field(..., min_length=6, max_length=128)


class DeleteAccountRequest(BaseModel):
    password: str = Field(..., min_length=6, max_length=128)
    confirm: bool = False


@router.post("/register")
def register(req: AuthRequest) -> dict:
    username = req.username.strip()
    if not username:
        raise HTTPException(status_code=400, detail="Invalid username")
    if get_user_by_username(username):
        raise HTTPException(status_code=409, detail="Username already exists")

    password_hash = hash_password(req.password)
    user = create_user(username=username, password_hash=password_hash)
    token = create_access_token(user_id=user["id"], username=user["username"])
    return {"token": token, "user": {"id": user["id"], "username": user["username"], "created_at": user["created_at"]}}


@router.post("/login")
def login(req: AuthRequest) -> dict:
    username = req.username.strip()
    user = get_user_by_username(username)
    if not user or user.get("deleted_at"):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    if not verify_password(req.password, user["password_hash"]):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    token = create_access_token(user_id=user["id"], username=user["username"])
    return {"token": token, "user": {"id": user["id"], "username": user["username"], "created_at": user["created_at"]}}


@router.post("/logout")
def logout() -> dict:
    return {"ok": True}


@router.get("/me")
def me(user: dict = Depends(get_current_user)) -> dict:
    return {"id": user["id"], "username": user["username"], "created_at": user.get("created_at")}


@router.delete("/me")
def delete_me(req: DeleteAccountRequest, user: dict = Depends(get_current_user)) -> dict:
    if not req.confirm:
        raise HTTPException(status_code=400, detail="Confirmation required")

    stored = get_user_by_id(user["id"])
    if not stored or not verify_password(req.password, stored["password_hash"]):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    delete_user(user["id"])
    delete_user_kb_files(user["id"])
    return {"ok": True}
