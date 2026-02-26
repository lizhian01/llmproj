from typing import List, Optional

from fastapi import APIRouter, File, Form, UploadFile, Depends

from server.api.deps import get_current_user
from server.services.kb_store import list_kbs, save_upload_files
from server.services.rag_service import build_index_for_kb

router = APIRouter(prefix="/api/kb", tags=["kb"])


@router.get("/list")
def list_kb(user: dict = Depends(get_current_user)) -> dict:
    return {"kbs": list_kbs(user["id"])}


@router.post("/upload")
async def upload_kb(
    files: List[UploadFile] = File(...),
    kb_id: Optional[str] = Form(None),
    kb_name: Optional[str] = Form(None),
    user: dict = Depends(get_current_user),
) -> dict:
    return await save_upload_files(user_id=user["id"], files=files, kb_id=kb_id, kb_name=kb_name)


@router.post("/{kb_id}/index")
def index_kb(kb_id: str, user: dict = Depends(get_current_user)) -> dict:
    stats = build_index_for_kb(user_id=user["id"], kb_id=kb_id)
    return {"ok": True, "kb_id": kb_id, "stats": stats}
