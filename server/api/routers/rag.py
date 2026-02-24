from fastapi import APIRouter
from pydantic import BaseModel, Field

from server.services.rag_service import ask_kb

router = APIRouter(prefix="/api/rag", tags=["rag"])


class RagAskRequest(BaseModel):
    kb_id: str = Field(..., min_length=1)
    question: str = Field(..., min_length=1)
    topk: int = Field(5, ge=1, le=50)
    threshold: float = Field(0.35, ge=0.0, le=1.0)
    embedding_model: str = Field("text-embedding-3-small")
    model: str = Field("gpt-4o-mini")


@router.post("/ask")
def ask(req: RagAskRequest) -> dict:
    return ask_kb(
        kb_id=req.kb_id,
        question=req.question,
        topk=req.topk,
        threshold=req.threshold,
        embedding_model=req.embedding_model,
        model=req.model,
    )
