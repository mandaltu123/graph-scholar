from app.services.chunking import chunk_pages


def test_chunking_basic():
    pages = [
        {"page_num": 1, "text": "INTRODUCTION\n" + "A " * 2000, "blocks": []},
        {"page_num": 2, "text": "METHODS\n" + "B " * 2000, "blocks": []},
    ]
    chunks = chunk_pages(pages, doc_id="doc-1", chunk_size_chars=500, overlap_chars=50)
    assert chunks
    assert all(chunk.metadata["doc_id"] == "doc-1" for chunk in chunks)
