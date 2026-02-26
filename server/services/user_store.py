import uuid
from datetime import datetime, timezone
from typing import Dict, List, Optional

from fastapi import HTTPException

from server.services.db import get_conn


def _now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _row_to_dict(row) -> Dict:
    return dict(row) if row else {}


def create_user(username: str, password_hash: str) -> Dict:
    if not username or not password_hash:
        raise HTTPException(status_code=400, detail="Invalid username or password")
    user_id = uuid.uuid4().hex
    created_at = _now_iso()
    try:
        with get_conn() as conn:
            conn.execute(
                "INSERT INTO users (id, username, password_hash, created_at, deleted_at) VALUES (?, ?, ?, ?, ?)",
                (user_id, username.strip(), password_hash, created_at, None),
            )
    except Exception:
        raise HTTPException(status_code=409, detail="Username already exists")
    return {"id": user_id, "username": username.strip(), "created_at": created_at, "deleted_at": None}


def get_user_by_username(username: str) -> Optional[Dict]:
    if not username:
        return None
    with get_conn() as conn:
        row = conn.execute(
            "SELECT id, username, password_hash, created_at, deleted_at FROM users WHERE username = ?",
            (username.strip(),),
        ).fetchone()
    return _row_to_dict(row) if row else None


def get_user_by_id(user_id: str) -> Optional[Dict]:
    if not user_id:
        return None
    with get_conn() as conn:
        row = conn.execute(
            "SELECT id, username, password_hash, created_at, deleted_at FROM users WHERE id = ?",
            (user_id,),
        ).fetchone()
    return _row_to_dict(row) if row else None


def delete_user(user_id: str) -> None:
    if not user_id:
        return
    with get_conn() as conn:
        conn.execute("DELETE FROM history_text WHERE user_id = ?", (user_id,))
        conn.execute("DELETE FROM history_rag WHERE user_id = ?", (user_id,))
        conn.execute("DELETE FROM kb_files WHERE user_id = ?", (user_id,))
        conn.execute("DELETE FROM kb WHERE user_id = ?", (user_id,))
        conn.execute("DELETE FROM users WHERE id = ?", (user_id,))


def _get_kb_row(user_id: str, kb_id: str) -> Optional[Dict]:
    with get_conn() as conn:
        row = conn.execute(
            "SELECT * FROM kb WHERE user_id = ? AND id = ?",
            (user_id, kb_id),
        ).fetchone()
    return _row_to_dict(row) if row else None


def upsert_kb_for_upload(user_id: str, kb_id: str, kb_name: Optional[str]) -> None:
    now = _now_iso()
    existing = _get_kb_row(user_id, kb_id)
    name = kb_name or kb_id
    if existing:
        with get_conn() as conn:
            conn.execute(
                """
                UPDATE kb
                SET name = ?, updated_at = ?, index_built = 0,
                    index_chunks = NULL, index_dir = NULL, chunks_path = NULL, index_updated_at = NULL
                WHERE user_id = ? AND id = ?
                """,
                (name if kb_name else existing.get("name", kb_id), now, user_id, kb_id),
            )
        return

    with get_conn() as conn:
        conn.execute(
            """
            INSERT INTO kb (id, user_id, name, created_at, updated_at, index_built)
            VALUES (?, ?, ?, ?, ?, 0)
            """,
            (kb_id, user_id, name, now, now),
        )


def add_kb_files(user_id: str, kb_id: str, files: List[Dict]) -> None:
    if not files:
        return
    with get_conn() as conn:
        for f in files:
            conn.execute(
                """
                INSERT INTO kb_files (id, kb_id, user_id, filename, rel_path, size, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    uuid.uuid4().hex,
                    kb_id,
                    user_id,
                    f.get("filename") or "",
                    f.get("rel_path") or "",
                    int(f.get("size") or 0),
                    f.get("uploaded_at") or _now_iso(),
                ),
            )


def set_kb_index(
    user_id: str,
    kb_id: str,
    *,
    built: bool,
    chunks: Optional[int] = None,
    index_dir: Optional[str] = None,
    chunks_path: Optional[str] = None,
) -> None:
    now = _now_iso()
    with get_conn() as conn:
        conn.execute(
            """
            UPDATE kb
            SET updated_at = ?, index_built = ?, index_chunks = ?, index_dir = ?,
                chunks_path = ?, index_updated_at = ?
            WHERE user_id = ? AND id = ?
            """,
            (
                now,
                1 if built else 0,
                chunks,
                index_dir,
                chunks_path,
                now,
                user_id,
                kb_id,
            ),
        )


def _kb_row_to_dict(row: Dict, files: List[Dict]) -> Dict:
    return {
        "kb_id": row.get("id"),
        "name": row.get("name"),
        "created_at": row.get("created_at"),
        "updated_at": row.get("updated_at"),
        "files": files,
        "index": {
            "built": bool(row.get("index_built")),
            "chunks": row.get("index_chunks"),
            "index_dir": row.get("index_dir"),
            "chunks_path": row.get("chunks_path"),
            "updated_at": row.get("index_updated_at"),
        },
    }


def list_kbs(user_id: str) -> List[Dict]:
    with get_conn() as conn:
        kb_rows = conn.execute(
            "SELECT * FROM kb WHERE user_id = ? ORDER BY updated_at DESC",
            (user_id,),
        ).fetchall()
        file_rows = conn.execute(
            """
            SELECT kb_id, filename, rel_path, size, created_at
            FROM kb_files
            WHERE user_id = ?
            ORDER BY created_at DESC
            """,
            (user_id,),
        ).fetchall()

    files_by_kb: Dict[str, List[Dict]] = {}
    for row in file_rows:
        kb_id = row["kb_id"]
        files_by_kb.setdefault(kb_id, []).append(
            {
                "filename": row["filename"],
                "rel_path": row["rel_path"],
                "size": row["size"],
                "uploaded_at": row["created_at"],
            }
        )

    return [_kb_row_to_dict(dict(row), files_by_kb.get(row["id"], [])) for row in kb_rows]


def get_kb_detail(user_id: str, kb_id: str) -> Optional[Dict]:
    row = _get_kb_row(user_id, kb_id)
    if not row:
        return None
    with get_conn() as conn:
        file_rows = conn.execute(
            """
            SELECT filename, rel_path, size, created_at
            FROM kb_files
            WHERE user_id = ? AND kb_id = ?
            ORDER BY created_at DESC
            """,
            (user_id, kb_id),
        ).fetchall()

    files = [
        {
            "filename": r["filename"],
            "rel_path": r["rel_path"],
            "size": r["size"],
            "uploaded_at": r["created_at"],
        }
        for r in file_rows
    ]
    return _kb_row_to_dict(row, files)
