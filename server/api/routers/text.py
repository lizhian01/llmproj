from fastapi import APIRouter
from pydantic import BaseModel, Field

from app.pipeline import process_text

router = APIRouter(prefix="/api/text", tags=["text"])


class TextProcessRequest(BaseModel):
    text: str = Field(..., min_length=1, description="Input text")


@router.post("/process")
def process(req: TextProcessRequest) -> dict:
    return process_text(req.text)
