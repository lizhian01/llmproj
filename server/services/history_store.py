import json
import os
import time
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from server.services.db import get_conn


DEFAULT_MAX_RECORDS = 100
PREVIEW_LEN = 120
ERROR_MESSAGE_MAX = 500
ERROR_TRACE_MAX = 2000


def _now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _now_ts_ms() -> int:
    return int(time.time() * 1000)


def _truncate(text: Optional[str], max_len: int) -> Optional[str]:
    if text is None:
        return None
    if len(text) <= max_len:
        return text
    return text[:max_len]


def _preview(text: Optional[str], max_len: int = PREVIEW_LEN) -> str:
    if not text:
        return ""
    compact = " ".join(text.strip().split())
    return _truncate(compact, max_len) or ""


def _parse_int(value: Optional[str], default: int) -> int:
    if value is None:
        return default
    try:
        parsed = int(value)
    except ValueError:
        return default
    return parsed if parsed > 0 else default


def get_max_records() -> int:
    raw = os.getenv("HISTORY_LIMIT") or os.getenv("HISTORY_MAX_RECORDS")
    return _parse_int(raw, DEFAULT_MAX_RECORDS)


def normalize_limit(limit: int) -> int:
    max_records = get_max_records()
    if limit <= 0:
        return max_records
    return min(limit, max_records)


def _trim_table(conn, table: str, user_id: str) -> None:
    max_records = get_max_records()
    conn.execute(
        f"""
        DELETE FROM {table}
        WHERE user_id = ?
        AND id NOT IN (
            SELECT id FROM {table}
            WHERE user_id = ?
            ORDER BY created_ts DESC
            LIMIT ?
        )
        """,
        (user_id, user_id, max_records),
    )


def _serialize_json(value: Optional[Any]) -> Optional[str]:
    if value is None:
        return None
    try:
        return json.dumps(value, ensure_ascii=False)
    except TypeError:
        return json.dumps(str(value), ensure_ascii=False)


def _parse_json(value: Optional[str], default: Any) -> Any:
    if not value:
        return default
    try:
        return json.loads(value)
    except json.JSONDecodeError:
        return default


def _error_fields(error: Optional[Exception], error_trace: Optional[str]) -> Dict[str, Optional[str]]:
    if not error:
        return {"error_type": None, "error_message": None, "error_trace": None}
    return {
        "error_type": type(error).__name__,
        "error_message": _truncate(str(error), ERROR_MESSAGE_MAX),
        "error_trace": _truncate(error_trace, ERROR_TRACE_MAX),
    }


def record_text_history(
    *,
    user_id: str,
    input_text: str,
    result: Optional[Dict[str, Any]],
    status: str,
    duration_ms: int,
    error: Optional[Exception] = None,
    error_trace: Optional[str] = None,
) -> str:
    history_id = uuid.uuid4().hex
    created_at = _now_iso()
    created_ts = _now_ts_ms()
    summary_short = result.get("summary_short") if result else None
    output_json = _serialize_json(result) if result else None

    errors = _error_fields(error, error_trace)

    with get_conn() as conn:
        conn.execute(
            """
            INSERT INTO history_text (
                id, user_id, created_at, created_ts, duration_ms, status,
                input_text, input_preview, summary_short, output_json,
                error_type, error_message, error_trace
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                history_id,
                user_id,
                created_at,
                created_ts,
                int(duration_ms),
                status,
                input_text,
                _preview(input_text),
                summary_short,
                output_json,
                errors["error_type"],
                errors["error_message"],
                errors["error_trace"],
            ),
        )
        _trim_table(conn, "history_text", user_id)
    return history_id


def record_rag_history(
    *,
    user_id: str,
    kb_id: str,
    question: str,
    topk: int,
    threshold: float,
    embedding_model: Optional[str],
    model: Optional[str],
    result: Optional[Dict[str, Any]],
    status: str,
    duration_ms: int,
    error: Optional[Exception] = None,
    error_trace: Optional[str] = None,
) -> str:
    history_id = uuid.uuid4().hex
    created_at = _now_iso()
    created_ts = _now_ts_ms()

    answer = result.get("answer") if result else None
    top_score = result.get("top_score") if result else None
    refused = result.get("refused") if result else None
    reason = result.get("reason") if result else None
    citations_json = _serialize_json(result.get("citations")) if result else None

    errors = _error_fields(error, error_trace)

    with get_conn() as conn:
        conn.execute(
            """
            INSERT INTO history_rag (
                id, user_id, kb_id, created_at, created_ts, duration_ms, status,
                question, question_preview, topk, threshold,
                embedding_model, model, refused, answer, answer_preview,
                top_score, citations_json, reason, error_type, error_message, error_trace
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                history_id,
                user_id,
                kb_id,
                created_at,
                created_ts,
                int(duration_ms),
                status,
                question,
                _preview(question),
                int(topk),
                float(threshold),
                embedding_model,
                model,
                1 if refused else 0 if refused is not None else None,
                answer,
                _preview(answer),
                top_score,
                citations_json,
                reason,
                errors["error_type"],
                errors["error_message"],
                errors["error_trace"],
            ),
        )
        _trim_table(conn, "history_rag", user_id)
    return history_id


def _row_to_dict(row) -> Dict[str, Any]:
    data = dict(row)
    if "refused" in data and data["refused"] is not None:
        data["refused"] = bool(data["refused"])
    return data


def list_text_history(user_id: str, limit: int) -> List[Dict[str, Any]]:
    safe_limit = normalize_limit(limit)
    with get_conn() as conn:
        rows = conn.execute(
            """
            SELECT id, created_at, created_ts, duration_ms, status,
                   input_preview, summary_short
            FROM history_text
            WHERE user_id = ?
            ORDER BY created_ts DESC
            LIMIT ?
            """,
            (user_id, safe_limit),
        ).fetchall()
    return [_row_to_dict(row) for row in rows]


def get_text_history(user_id: str, history_id: str) -> Optional[Dict[str, Any]]:
    with get_conn() as conn:
        row = conn.execute(
            "SELECT * FROM history_text WHERE id = ? AND user_id = ?",
            (history_id, user_id),
        ).fetchone()
    return _row_to_dict(row) if row else None


def list_rag_history(user_id: str, limit: int) -> List[Dict[str, Any]]:
    safe_limit = normalize_limit(limit)
    with get_conn() as conn:
        rows = conn.execute(
            """
            SELECT id, created_at, created_ts, duration_ms, status, kb_id,
                   question_preview, answer_preview, refused, top_score, threshold
            FROM history_rag
            WHERE user_id = ?
            ORDER BY created_ts DESC
            LIMIT ?
            """,
            (user_id, safe_limit),
        ).fetchall()
    return [_row_to_dict(row) for row in rows]


def get_rag_history(user_id: str, history_id: str) -> Optional[Dict[str, Any]]:
    with get_conn() as conn:
        row = conn.execute(
            "SELECT * FROM history_rag WHERE id = ? AND user_id = ?",
            (history_id, user_id),
        ).fetchone()
    if not row:
        return None
    data = _row_to_dict(row)
    data["citations"] = _parse_json(data.get("citations_json"), [])
    return data
