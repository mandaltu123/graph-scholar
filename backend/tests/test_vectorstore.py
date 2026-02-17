from app.core.config import get_settings
from app.services.vectorstore import count_chunks, get_collection, upsert_chunks


def test_vectorstore_ingestion(tmp_path, monkeypatch):
    monkeypatch.setenv("CHROMA_PERSIST_DIR", str(tmp_path / "chroma"))
    get_settings.cache_clear()
    get_collection.cache_clear()
    upsert_chunks(
        ids=["doc-1:p1-c0"],
        documents=["Example text"],
        embeddings=[[0.1, 0.2, 0.3]],
        metadatas=[{"doc_id": "doc-1", "page_num": 1, "chunk_ref": "p1-c0"}],
    )
    assert count_chunks("doc-1") == 1
