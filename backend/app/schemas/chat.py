from __future__ import annotations

from typing import List, Optional

from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    doc_id: str
    session_id: str
    message: str
    top_k: int = Field(5, ge=1, le=20)


class SourceChunk(BaseModel):
    chunk_id: str
    text: str
    page_num: Optional[int] = None
    score: float
    metadata: dict


class ChatResponse(BaseModel):
    answer: str
    sources: List[SourceChunk]
    related_questions: List[str]
    verified: bool
    verification_notes: str
