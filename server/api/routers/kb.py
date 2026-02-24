from typing import List, Optional

from fastapi import APIRouter, File, Form, UploadFile

from server.services.kb_store import list_kbs, save_upload_files
from server.services.rag_service import build_index_for_kb

router = APIRouter(prefix="/api/kb", tags=["kb"])


@router.get("/list")
def list_kb() -> dict:
    return {"kbs": list_kbs()}


@router.post("/upload")
async def upload_kb(
    files: List[UploadFile] = File(...),
    kb_id: Optional[str] = Form(None),
    kb_name: Optional[str] = Form(None),
) -> dict:
    return await save_upload_files(files=files, kb_id=kb_id, kb_name=kb_name)


@router.post("/{kb_id}/index")
def index_kb(kb_id: str) -> dict:
    stats = build_index_for_kb(kb_id=kb_id)
    return {"ok": True, "kb_id": kb_id, "stats": stats}
