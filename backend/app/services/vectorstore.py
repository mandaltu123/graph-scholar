from __future__ import annotations

from functools import lru_cache
from typing import Dict, List, Optional

import chromadb
from chromadb.config import Settings as ChromaSettings
from pydantic import BaseModel

from app.core.config import get_settings


def _ensure_pydantic_compat() -> None:
    if not hasattr(BaseModel, "model_fields"):
        BaseModel.model_fields = property(lambda self: self.__fields__)


def _get_client() -> chromadb.PersistentClient:
    _ensure_pydantic_compat()
    settings = get_settings()
    return chromadb.PersistentClient(
        path=settings.chroma_persist_dir,
        settings=ChromaSettings(anonymized_telemetry=False),
    )


@lru_cache
def get_collection():
    client = _get_client()
    settings = get_settings()
    return client.get_or_create_collection(settings.chroma_collection)


def upsert_chunks(
    ids: List[str], documents: List[str], embeddings: List[List[float]], metadatas: List[dict]
) -> None:
    collection = get_collection()
    collection.upsert(
        ids=ids,
        documents=documents,
        embeddings=embeddings,
        metadatas=metadatas,
    )


def query_chunks(embedding: List[float], top_k: int, doc_id: Optional[str]) -> dict:
    collection = get_collection()
    where = {"doc_id": doc_id} if doc_id else None
    return collection.query(
        query_embeddings=[embedding],
        n_results=top_k,
        where=where,
        include=["documents", "metadatas", "distances"],
    )


def get_chunks(where: Optional[Dict] = None, limit: int = 10) -> dict:
    collection = get_collection()
    return collection.get(where=where, limit=limit, include=["documents", "metadatas"])


def count_chunks(doc_id: Optional[str]) -> int:
    collection = get_collection()
    where = {"doc_id": doc_id} if doc_id else None
    return collection.count(where=where)
