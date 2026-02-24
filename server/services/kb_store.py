import re
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from fastapi import HTTPException, UploadFile

from server.services.manifest import ensure_manifest, find_kb, save_manifest, upsert_kb
from server.services.paths import KBS_DIR


KB_ID_RE = re.compile(r"^[A-Za-z0-9_-]+$")


def _now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def validate_kb_id(kb_id: str) -> str:
    if not kb_id or not KB_ID_RE.match(kb_id):
        raise HTTPException(status_code=400, detail="Invalid kb_id")
    return kb_id


def create_kb_id() -> str:
    stamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    return f"kb_{stamp}_{uuid.uuid4().hex[:8]}"


def get_kb_root(kb_id: str) -> Path:
    return KBS_DIR / kb_id


def get_kb_dir(kb_id: str) -> Path:
    return get_kb_root(kb_id) / "raw"


def get_kb_index_paths(kb_id: str) -> Tuple[Path, Path]:
    root = get_kb_root(kb_id)
    return root / "index", root / "chunks.json"


def list_kbs() -> List[Dict]:
    manifest = ensure_manifest()
    return manifest.get("kbs", [])


async def save_upload_files(
    files: List[UploadFile],
    kb_id: Optional[str] = None,
    kb_name: Optional[str] = None,
) -> Dict:
    if not files:
        raise HTTPException(status_code=400, detail="No files uploaded")

    manifest = ensure_manifest()

    if kb_id:
        kb_id = validate_kb_id(kb_id)
    else:
        kb_id = create_kb_id()

    kb_dir = get_kb_dir(kb_id)
    kb_dir.mkdir(parents=True, exist_ok=True)

    saved_files: List[Dict] = []
    for f in files:
        if not f.filename:
            continue
        data = await f.read()
        safe_name = Path(f.filename).name
        dest = kb_dir / safe_name
        dest.write_bytes(data)
        saved_files.append({
            "filename": safe_name,
            "size": len(data),
            "uploaded_at": _now_iso(),
        })

    if not saved_files:
        raise HTTPException(status_code=400, detail="No valid files uploaded")

    existing = find_kb(manifest, kb_id)
    now = _now_iso()
    if existing:
        existing_files = existing.get("files", [])
        existing_files.extend(saved_files)
        existing["files"] = existing_files
        existing["updated_at"] = now
        if kb_name:
            existing["name"] = kb_name
        if existing.get("index"):
            existing["index"]["built"] = False
    else:
        existing = {
            "kb_id": kb_id,
            "name": kb_name or kb_id,
            "created_at": now,
            "updated_at": now,
            "files": saved_files,
            "index": {"built": False},
        }

    upsert_kb(manifest, existing)
    save_manifest(manifest)

    return {
        "ok": True,
        "kb_id": kb_id,
        "files": saved_files,
        "kb": existing,
    }
