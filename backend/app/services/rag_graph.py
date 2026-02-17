from __future__ import annotations

import json
from typing import Any, Dict, List, Optional, TypedDict
import re

from langgraph.graph import END, StateGraph

from app.core.config import get_settings
from app.services.embeddings import embed_query
from app.services.llm_client import get_llm_client
from app.services.prompts import (
    SYSTEM_CLASSIFIER,
    SYSTEM_GENERATE,
    SYSTEM_RELATED,
)
from app.services.vectorstore import query_chunks
from app.services.verifier import heuristic_grounding, verify_answer


class RAGState(TypedDict, total=False):
    doc_id: str
    session_id: str
    question: str
    chat_history: List[Dict[str, str]]
    retrieved_chunks: List[Dict[str, Any]]
    draft_answer: str
    verified: bool
    retries: int
    final_answer: str
    related_questions: List[str]
    verification_notes: str
    needs_retrieval: bool
    top_k: int


class SessionMemory:
    def __init__(self) -> None:
        self._store: Dict[str, List[Dict[str, str]]] = {}

    def get(self, session_id: str, limit: int) -> List[Dict[str, str]]:
        history = self._store.get(session_id, [])
        return history[-limit:]

    def append(self, session_id: str, role: str, content: str, limit: int) -> None:
        history = self._store.setdefault(session_id, [])
        history.append({"role": role, "content": content})
        if len(history) > limit:
            self._store[session_id] = history[-limit:]


memory = SessionMemory()


def classify_query(state: RAGState) -> RAGState:
    question = state["question"].lower()
    app_keywords = ["app", "ui", "upload", "system", "feature", "how do i use"]
    if any(keyword in question for keyword in app_keywords):
        return {"needs_retrieval": False}
    if state.get("doc_id"):
        return {"needs_retrieval": True}
    client = get_llm_client()
    messages = [
        {"role": "system", "content": SYSTEM_CLASSIFIER},
        {"role": "user", "content": state["question"]},
    ]
    result = client.chat(messages).strip().upper()
    if result == "GENERAL":
        return {"needs_retrieval": False}
    return {"needs_retrieval": True}


def retrieve(state: RAGState) -> RAGState:
    settings = get_settings()
    if not state.get("needs_retrieval", True):
        return {"retrieved_chunks": []}
    embedding = embed_query(state["question"])
    top_k = state.get("top_k") or settings.default_top_k
    result = query_chunks(embedding, top_k, state["doc_id"])
    ids = result.get("ids", [[]])[0]
    documents = result.get("documents", [[]])[0]
    metadatas = result.get("metadatas", [[]])[0]
    distances = result.get("distances", [[]])[0]
    chunks = []
    for idx, chunk_id in enumerate(ids):
        metadata = metadatas[idx] or {}
        chunks.append(
            {
                "chunk_id": chunk_id,
                "text": documents[idx],
                "score": float(distances[idx]) if idx < len(distances) else 0.0,
                "metadata": metadata,
            }
        )
    return {"retrieved_chunks": chunks}


def _build_context(chunks: List[Dict[str, Any]]) -> str:
    parts = []
    for chunk in chunks:
        meta = chunk.get("metadata", {})
        chunk_ref = meta.get("chunk_ref") or chunk.get("chunk_id")
        label = f"[{chunk_ref}]"
        parts.append(f"{label}\n{chunk.get('text', '')}")
    return "\n\n".join(parts)


def generate(state: RAGState) -> RAGState:
    settings = get_settings()
    client = get_llm_client()
    chunks = state.get("retrieved_chunks", [])
    context = _build_context(chunks)
    if len(context) > settings.max_context_chars:
        context = context[: settings.max_context_chars] + "\n\n[Truncated]"

    history = state.get("chat_history", [])
    messages = [{"role": "system", "content": SYSTEM_GENERATE}]
    messages.extend(history)
    messages.append(
        {
            "role": "user",
            "content": f"Context:\n{context}\n\nQuestion: {state['question']}",
        }
    )
    answer = client.chat(messages)
    answer = _ensure_citations(answer, chunks)
    return {"draft_answer": answer}


def verify(state: RAGState) -> RAGState:
    chunks = state.get("retrieved_chunks", [])
    context = _build_context(chunks)
    llm_result = verify_answer(state.get("draft_answer", ""), context)
    heuristic = heuristic_grounding(
        state.get("draft_answer", ""),
        [chunk.get("metadata", {}).get("chunk_ref", chunk["chunk_id"]) for chunk in chunks],
    )
    grounded = bool(llm_result.get("grounded")) and heuristic["ok"]
    notes = llm_result.get("unsupported_claims") or []
    if not heuristic["ok"]:
        notes.append(heuristic["notes"])
    return {
        "verified": grounded,
        "verification_notes": "; ".join([str(n) for n in notes if n]),
        "retries": state.get("retries", 0),
    }


def refine(state: RAGState) -> RAGState:
    settings = get_settings()
    client = get_llm_client()
    retries = state.get("retries", 0) + 1
    chunks = state.get("retrieved_chunks", [])
    context = _build_context(chunks)
    fix = state.get("verification_notes", "")
    messages = [
        {
            "role": "system",
            "content": (
                SYSTEM_GENERATE
                + " Be extra strict. Every sentence must include citations."
            ),
        },
        {
            "role": "user",
            "content": (
                f"Context:\n{context}\n\nQuestion: {state['question']}\n\n"
                f"Verifier feedback: {fix}"
            ),
        },
    ]
    answer = client.chat(messages, max_tokens=settings.llm_max_tokens)
    answer = _ensure_citations(answer, chunks)
    return {"draft_answer": answer, "retries": retries}


def related_qs(state: RAGState) -> RAGState:
    client = get_llm_client()
    chunks = state.get("retrieved_chunks", [])
    context = _build_context(chunks)
    messages = [
        {"role": "system", "content": SYSTEM_RELATED},
        {"role": "user", "content": f"Context:\n{context}"},
    ]
    raw = client.chat(messages)
    try:
        items = json.loads(raw)
        if isinstance(items, list):
            related = [str(item) for item in items if str(item).strip()]
        else:
            related = []
    except json.JSONDecodeError:
        related = []
    return {"related_questions": related[:5]}


def _ensure_citations(answer: str, chunks: List[Dict[str, Any]]) -> str:
    if not chunks:
        return answer
    pattern = re.compile(r"\[p\d+-c\d+\]")
    if pattern.search(answer):
        return answer
    top_ref = chunks[0].get("metadata", {}).get("chunk_ref")
    if not top_ref:
        top_ref = chunks[0].get("chunk_id", "")
    if not top_ref:
        return answer
    return f"{answer.strip()} [{top_ref}]"


def _should_retry(state: RAGState) -> str:
    settings = get_settings()
    if not state.get("verified") and state.get("retries", 0) < settings.max_retries:
        return "retry"
    return "final"


def _finalize(state: RAGState) -> RAGState:
    if state.get("verified"):
        return {"final_answer": state.get("draft_answer", "")}
    chunks = state.get("retrieved_chunks", [])
    if chunks:
        top = chunks[0]
        text = top.get("text", "").strip()
        summary = text.split(". ")
        snippet = ". ".join(summary[:2]).strip()
        if snippet and not snippet.endswith("."):
            snippet += "."
        ref = top.get("metadata", {}).get("chunk_ref", top.get("chunk_id", ""))
        if snippet:
            return {"final_answer": f"{snippet} [{ref}]"}
    return {
        "final_answer": (
            "I cannot confirm the answer from the provided document context."
        )
    }


def build_graph() -> StateGraph:
    graph = StateGraph(RAGState)
    graph.add_node("classify_query", classify_query)
    graph.add_node("retrieve", retrieve)
    graph.add_node("generate", generate)
    graph.add_node("verify", verify)
    graph.add_node("refine", refine)
    graph.add_node("related_qs", related_qs)
    graph.add_node("finalize", _finalize)

    graph.set_entry_point("classify_query")
    graph.add_edge("classify_query", "retrieve")
    graph.add_edge("retrieve", "generate")
    graph.add_edge("generate", "verify")
    graph.add_conditional_edges("verify", _should_retry, {"retry": "refine", "final": "finalize"})
    graph.add_edge("refine", "verify")
    graph.add_edge("finalize", "related_qs")
    graph.add_edge("related_qs", END)
    return graph


def run_graph(
    doc_id: str,
    session_id: str,
    question: str,
    chat_history: List[Dict[str, str]],
    top_k: int,
) -> RAGState:
    settings = get_settings()
    history = chat_history[-settings.session_history_max :]
    state: RAGState = {
        "doc_id": doc_id,
        "session_id": session_id,
        "question": question,
        "chat_history": history,
        "retries": 0,
        "verified": False,
        "top_k": top_k,
    }
    graph = build_graph().compile()
    return graph.invoke(state)
