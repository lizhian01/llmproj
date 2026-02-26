from time import perf_counter
import traceback

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field

from app.pipeline import process_text
from server.api.deps import get_current_user
from server.services.external_errors import raise_external_error
from server.services.history_store import (
    get_text_history,
    list_text_history,
    normalize_limit,
    record_text_history,
)

router = APIRouter(prefix="/api/text", tags=["text"])


class TextProcessRequest(BaseModel):
    text: str = Field(..., min_length=1, description="Input text")


@router.post("/process")
def process(req: TextProcessRequest, user: dict = Depends(get_current_user)) -> dict:
    start = perf_counter()
    try:
        result = process_text(req.text)
    except Exception as exc:
        duration_ms = int((perf_counter() - start) * 1000)
        try:
            record_text_history(
                user_id=user["id"],
                input_text=req.text,
                result=None,
                status="error",
                duration_ms=duration_ms,
                error=exc,
                error_trace=traceback.format_exc(),
            )
        except Exception:
            pass
        raise_external_error(exc, action="text processing")
    duration_ms = int((perf_counter() - start) * 1000)
    try:
        record_text_history(
            user_id=user["id"],
            input_text=req.text,
            result=result,
            status="success",
            duration_ms=duration_ms,
        )
    except Exception:
        pass
    return result


@router.get("/history")
def list_history(limit: int = 50, user: dict = Depends(get_current_user)) -> dict:
    safe_limit = normalize_limit(limit)
    items = list_text_history(user["id"], safe_limit)
    return {"items": items, "limit": safe_limit}


@router.get("/history/{history_id}")
def history_detail(history_id: str, user: dict = Depends(get_current_user)) -> dict:
    item = get_text_history(user["id"], history_id)
    if not item:
        raise HTTPException(status_code=404, detail="History record not found")
    return item
