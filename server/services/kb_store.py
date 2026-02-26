import os
import re
import shutil
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from fastapi import HTTPException, UploadFile

from server.services.paths import KBS_DIR
from server.services.user_store import add_kb_files, get_kb_detail, list_kbs as list_kbs_for_user, upsert_kb_for_upload


KB_ID_RE = re.compile(r"^[A-Za-z0-9_-]+$")
ALLOWED_UPLOAD_SUFFIXES = {".md", ".txt"}
MAX_UPLOAD_BYTES = int(os.getenv("KB_MAX_UPLOAD_BYTES", str(10 * 1024 * 1024)))
UPLOAD_CHUNK_SIZE = 1024 * 1024


def _now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def validate_kb_id(kb_id: str) -> str:
    if not kb_id or not KB_ID_RE.match(kb_id):
        raise HTTPException(status_code=400, detail="Invalid kb_id")
    return kb_id


def create_kb_id() -> str:
    stamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    return f"kb_{stamp}_{uuid.uuid4().hex[:8]}"


def _safe_user_id(user_id: str) -> str:
    if not user_id:
        raise HTTPException(status_code=400, detail="Invalid user")
    return user_id


def get_user_root(user_id: str) -> Path:
    user_id = _safe_user_id(user_id)
    return KBS_DIR / user_id


def get_kb_root(user_id: str, kb_id: str) -> Path:
    kb_id = validate_kb_id(kb_id)
    return get_user_root(user_id) / kb_id


def get_kb_dir(user_id: str, kb_id: str) -> Path:
    return get_kb_root(user_id, kb_id) / "raw"


def get_kb_index_paths(user_id: str, kb_id: str) -> Tuple[Path, Path]:
    root = get_kb_root(user_id, kb_id)
    return root / "index", root / "chunks.json"


def list_kbs(user_id: str) -> List[Dict]:
    return list_kbs_for_user(user_id)


def delete_user_kb_files(user_id: str) -> None:
    root = get_user_root(user_id)
    if root.exists():
        shutil.rmtree(root, ignore_errors=True)


async def _save_upload_file(upload: UploadFile, dest: Path) -> int:
    total = 0
    with dest.open("wb") as out:
        while True:
            chunk = await upload.read(UPLOAD_CHUNK_SIZE)
            if not chunk:
                break
            total += len(chunk)
            if total > MAX_UPLOAD_BYTES:
                out.close()
                dest.unlink(missing_ok=True)
                raise HTTPException(
                    status_code=400,
                    detail=f"File too large: {upload.filename} (max {MAX_UPLOAD_BYTES} bytes)",
                )
            out.write(chunk)
    await upload.close()
    return total


async def save_upload_files(
    *,
    user_id: str,
    files: List[UploadFile],
    kb_id: Optional[str] = None,
    kb_name: Optional[str] = None,
) -> Dict:
    if not files:
        raise HTTPException(status_code=400, detail="No files uploaded")

    if kb_id:
        kb_id = validate_kb_id(kb_id)
    else:
        kb_id = create_kb_id()

    kb_dir = get_kb_dir(user_id, kb_id)
    kb_dir.mkdir(parents=True, exist_ok=True)

    saved_files: List[Dict] = []
    for f in files:
        if not f.filename:
            await f.close()
            continue
        safe_name = Path(f.filename).name
        suffix = Path(safe_name).suffix.lower()
        if suffix not in ALLOWED_UPLOAD_SUFFIXES:
            await f.close()
            continue
        dest = kb_dir / safe_name
        size = await _save_upload_file(f, dest)
        saved_files.append({
            "filename": safe_name,
            "size": size,
            "uploaded_at": _now_iso(),
        })

    if not saved_files:
        raise HTTPException(status_code=400, detail="No valid files uploaded")

    upsert_kb_for_upload(user_id, kb_id, kb_name)
    db_files = [
        {
            "filename": f["filename"],
            "size": f["size"],
            "uploaded_at": f["uploaded_at"],
            "rel_path": f"raw/{f['filename']}",
        }
        for f in saved_files
    ]
    add_kb_files(user_id, kb_id, db_files)

    kb = get_kb_detail(user_id, kb_id)

    return {
        "ok": True,
        "kb_id": kb_id,
        "files": saved_files,
        "kb": kb,
    }
