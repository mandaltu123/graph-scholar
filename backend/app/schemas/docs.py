from __future__ import annotations

from typing import Optional

from pydantic import BaseModel


class DocStatusResponse(BaseModel):
    doc_id: str
    filename: str
    status: str
    chunk_count: int
    embedded: bool
    created_at: str
    updated_at: str
    embedding_model: Optional[str] = None
    error: Optional[str] = None


class ChunkPreview(BaseModel):
    chunk_id: str
    text: str
    page_num: Optional[int] = None
    metadata: dict


class DocChunksResponse(BaseModel):
    doc_id: str
    count: int
    chunks: list[ChunkPreview]
