from __future__ import annotations

from fastapi import APIRouter, HTTPException

from app.schemas.chat import ChatRequest, ChatResponse, SourceChunk
from app.services.doc_store import DocStore
from app.services.rag_graph import memory, run_graph

router = APIRouter()


@router.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest) -> ChatResponse:
    store = DocStore()
    doc = store.get(request.doc_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found.")
    if doc.get("status") != "Ready":
        raise HTTPException(status_code=400, detail="Document not indexed yet.")

    history = memory.get(request.session_id, limit=10)
    state = run_graph(
        doc_id=request.doc_id,
        session_id=request.session_id,
        question=request.message,
        chat_history=history,
        top_k=request.top_k,
    )
    memory.append(request.session_id, "user", request.message, limit=10)
    memory.append(
        request.session_id, "assistant", state.get("final_answer", ""), limit=10
    )

    sources = []
    for chunk in state.get("retrieved_chunks", []):
        metadata = chunk.get("metadata", {})
        sources.append(
            SourceChunk(
                chunk_id=metadata.get("chunk_ref", chunk.get("chunk_id", "")),
                text=chunk.get("text", ""),
                page_num=metadata.get("page_num"),
                score=float(chunk.get("score", 0.0)),
                metadata=metadata,
            )
        )

    return ChatResponse(
        answer=state.get("final_answer", ""),
        sources=sources,
        related_questions=state.get("related_questions", []),
        verified=bool(state.get("verified")),
        verification_notes=state.get("verification_notes", ""),
    )
