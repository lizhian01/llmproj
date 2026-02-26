from time import perf_counter
import traceback

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field

from server.api.deps import get_current_user
from server.services.rag_service import ask_kb
from server.services.history_store import (
    get_rag_history,
    list_rag_history,
    normalize_limit,
    record_rag_history,
)

router = APIRouter(prefix="/api/rag", tags=["rag"])


class RagAskRequest(BaseModel):
    kb_id: str = Field(..., min_length=1)
    question: str = Field(..., min_length=1)
    topk: int = Field(5, ge=1, le=50)
    threshold: float = Field(0.35, ge=0.0, le=1.0)
    embedding_model: str = Field("text-embedding-3-small")
    model: str = Field("gpt-4o-mini")


@router.post("/ask")
def ask(req: RagAskRequest, user: dict = Depends(get_current_user)) -> dict:
    start = perf_counter()
    try:
        result = ask_kb(
            user_id=user["id"],
            kb_id=req.kb_id,
            question=req.question,
            topk=req.topk,
            threshold=req.threshold,
            embedding_model=req.embedding_model,
            model=req.model,
        )
    except Exception as exc:
        duration_ms = int((perf_counter() - start) * 1000)
        try:
            record_rag_history(
                user_id=user["id"],
                kb_id=req.kb_id,
                question=req.question,
                topk=req.topk,
                threshold=req.threshold,
                embedding_model=req.embedding_model,
                model=req.model,
                result=None,
                status="error",
                duration_ms=duration_ms,
                error=exc,
                error_trace=traceback.format_exc(),
            )
        except Exception:
            pass
        raise

    duration_ms = int((perf_counter() - start) * 1000)
    status = "refused" if result.get("refused") else "success"
    try:
        record_rag_history(
            user_id=user["id"],
            kb_id=req.kb_id,
            question=req.question,
            topk=req.topk,
            threshold=req.threshold,
            embedding_model=req.embedding_model,
            model=req.model,
            result=result,
            status=status,
            duration_ms=duration_ms,
        )
    except Exception:
        pass
    return result


@router.get("/history")
def list_history(limit: int = 50, user: dict = Depends(get_current_user)) -> dict:
    safe_limit = normalize_limit(limit)
    items = list_rag_history(user["id"], safe_limit)
    return {"items": items, "limit": safe_limit}


@router.get("/history/{history_id}")
def history_detail(history_id: str, user: dict = Depends(get_current_user)) -> dict:
    item = get_rag_history(user["id"], history_id)
    if not item:
        raise HTTPException(status_code=404, detail="History record not found")
    return item
