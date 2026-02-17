from __future__ import annotations

from functools import lru_cache
from typing import List

from sentence_transformers import SentenceTransformer

from app.core.config import get_settings


@lru_cache
def _get_model() -> SentenceTransformer:
    settings = get_settings()
    return SentenceTransformer(settings.embedding_model)


def embed_texts(texts: List[str]) -> List[List[float]]:
    model = _get_model()
    embeddings = model.encode(texts, show_progress_bar=False, convert_to_numpy=True)
    return embeddings.tolist()


def embed_query(text: str) -> List[float]:
    return embed_texts([text])[0]
