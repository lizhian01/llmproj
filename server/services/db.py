import os
import sqlite3
from pathlib import Path

from server.services.paths import BASE_DIR, DATA_DIR


SCHEMA_VERSION = 2


def _resolve_db_path() -> Path:
    env_path = os.getenv("DB_PATH")
    if not env_path:
        env_path = os.getenv("HISTORY_DB_PATH")
    if env_path:
        path = Path(env_path)
        if not path.is_absolute():
            path = (BASE_DIR / path).resolve()
        return path
    return DATA_DIR / "app.db"


def get_db_path() -> Path:
    return _resolve_db_path()


def _ensure_schema(conn: sqlite3.Connection) -> None:
    cur = conn.execute("PRAGMA user_version")
    row = cur.fetchone()
    version = row[0] if row else 0
    if version >= SCHEMA_VERSION:
        return

    conn.executescript(
        """
        CREATE TABLE IF NOT EXISTS users (
            id TEXT PRIMARY KEY,
            username TEXT NOT NULL UNIQUE COLLATE NOCASE,
            password_hash TEXT NOT NULL,
            created_at TEXT NOT NULL,
            deleted_at TEXT
        );
        CREATE INDEX IF NOT EXISTS idx_users_username ON users (username);

        CREATE TABLE IF NOT EXISTS kb (
            id TEXT NOT NULL,
            user_id TEXT NOT NULL,
            name TEXT NOT NULL,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL,
            index_built INTEGER NOT NULL DEFAULT 0,
            index_chunks INTEGER,
            index_dir TEXT,
            chunks_path TEXT,
            index_updated_at TEXT,
            UNIQUE (user_id, id)
        );
        CREATE INDEX IF NOT EXISTS idx_kb_user_updated ON kb (user_id, updated_at);

        CREATE TABLE IF NOT EXISTS kb_files (
            id TEXT PRIMARY KEY,
            kb_id TEXT NOT NULL,
            user_id TEXT NOT NULL,
            filename TEXT NOT NULL,
            rel_path TEXT NOT NULL,
            size INTEGER NOT NULL,
            created_at TEXT NOT NULL
        );
        CREATE INDEX IF NOT EXISTS idx_kb_files_user_kb ON kb_files (user_id, kb_id);

        CREATE TABLE IF NOT EXISTS history_text (
            id TEXT PRIMARY KEY,
            user_id TEXT NOT NULL,
            created_at TEXT NOT NULL,
            created_ts INTEGER NOT NULL,
            duration_ms INTEGER NOT NULL,
            status TEXT NOT NULL,
            input_text TEXT NOT NULL,
            input_preview TEXT NOT NULL,
            summary_short TEXT,
            output_json TEXT,
            error_type TEXT,
            error_message TEXT,
            error_trace TEXT
        );
        CREATE INDEX IF NOT EXISTS idx_history_text_user_ts
            ON history_text (user_id, created_ts DESC);

        CREATE TABLE IF NOT EXISTS history_rag (
            id TEXT PRIMARY KEY,
            user_id TEXT NOT NULL,
            kb_id TEXT NOT NULL,
            created_at TEXT NOT NULL,
            created_ts INTEGER NOT NULL,
            duration_ms INTEGER NOT NULL,
            status TEXT NOT NULL,
            question TEXT NOT NULL,
            question_preview TEXT NOT NULL,
            topk INTEGER,
            threshold REAL,
            embedding_model TEXT,
            model TEXT,
            refused INTEGER,
            answer TEXT,
            answer_preview TEXT,
            top_score REAL,
            citations_json TEXT,
            reason TEXT,
            error_type TEXT,
            error_message TEXT,
            error_trace TEXT
        );
        CREATE INDEX IF NOT EXISTS idx_history_rag_user_ts
            ON history_rag (user_id, created_ts DESC);
        """
    )
    conn.execute(f"PRAGMA user_version = {SCHEMA_VERSION}")
    conn.commit()


def get_conn() -> sqlite3.Connection:
    path = get_db_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(path))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    _ensure_schema(conn)
    return conn
