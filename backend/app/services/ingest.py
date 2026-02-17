from __future__ import annotations

import logging
from pathlib import Path
from typing import List

from app.core.config import get_settings
from app.services.chunking import Chunk, chunk_pages
from app.services.doc_store import DocStore
from app.services.embeddings import embed_texts
from app.services.ocr_landingai import extract_pdf
from app.services.vectorstore import upsert_chunks

logger = logging.getLogger(__name__)


def ingest_document(doc_id: str, filename: str, pdf_path: Path) -> List[Chunk]:
    settings = get_settings()
    store = DocStore()
    try:
        ocr_data = extract_pdf(pdf_path, doc_id)
        pages = ocr_data.get("pages", [])
        chunks = chunk_pages(
            pages,
            doc_id=doc_id,
            chunk_size_chars=settings.chunk_size_chars,
            overlap_chars=settings.chunk_overlap_chars,
        )
        if not chunks:
            raise RuntimeError(
                "No chunks produced from OCR text. Check LandingAI endpoint response."
            )
        embeddings = embed_texts([chunk.text for chunk in chunks])
        metadatas = [chunk.metadata for chunk in chunks]
        upsert_chunks(
            ids=[chunk.chunk_id for chunk in chunks],
            documents=[chunk.text for chunk in chunks],
            embeddings=embeddings,
            metadatas=metadatas,
        )
        store.update(
            doc_id,
            status="Ready",
            chunk_count=len(chunks),
            embedded=True,
            embedding_model=settings.embedding_model,
            error=None,
        )
        logger.info("Ingested %s chunks for doc_id=%s", len(chunks), doc_id)
        return chunks
    except Exception as exc:
        logger.exception("Ingestion failed for doc_id=%s", doc_id)
        store.update(doc_id, status="Error", embedded=False, error=str(exc))
        raise
