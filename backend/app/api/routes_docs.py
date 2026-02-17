from __future__ import annotations

from fastapi import APIRouter, HTTPException
from typing import List, Optional
from pydantic import BaseModel

from app.schemas.docs import DocStatusResponse, DocChunksResponse, ChunkPreview
from app.services.doc_store import DocStore
from app.services.vectorstore import get_chunks

router = APIRouter()


class LegacyPaperInfo(BaseModel):
    paper_id: str
    filename: str
    status: str
    error: Optional[str] = None


@router.get("/docs/{doc_id}/status", response_model=DocStatusResponse)
async def doc_status(doc_id: str) -> DocStatusResponse:
    store = DocStore()
    data = store.get(doc_id)
    if not data:
        raise HTTPException(status_code=404, detail="Document not found.")
    return DocStatusResponse(**data)


@router.get("/docs/{doc_id}/chunks", response_model=DocChunksResponse)
async def doc_chunks(doc_id: str, limit: int = 5) -> DocChunksResponse:
    data = get_chunks(where={"doc_id": doc_id}, limit=limit)
    ids = data.get("ids", [])
    chunks = []
    for chunk_id, text, metadata in zip(
        ids, data.get("documents", []), data.get("metadatas", [])
    ):
        chunks.append(
            ChunkPreview(
                chunk_id=chunk_id,
                text=text or "",
                page_num=(metadata or {}).get("page_num"),
                metadata=metadata or {},
            )
        )
    return DocChunksResponse(doc_id=doc_id, count=len(ids), chunks=chunks)


@router.get("/papers", response_model=List[LegacyPaperInfo])
async def list_papers() -> List[LegacyPaperInfo]:
    store = DocStore()
    items = list(store.list().values())
    return [
        LegacyPaperInfo(
            paper_id=item["doc_id"],
            filename=item["filename"],
            status=item["status"],
            error=item.get("error"),
        )
        for item in items
    ]


@router.get("/papers/{doc_id}", response_model=LegacyPaperInfo)
async def get_paper(doc_id: str) -> LegacyPaperInfo:
    store = DocStore()
    data = store.get(doc_id)
    if not data:
        raise HTTPException(status_code=404, detail="Document not found.")
    return LegacyPaperInfo(
        paper_id=data["doc_id"],
        filename=data["filename"],
        status=data["status"],
        error=data.get("error"),
    )
