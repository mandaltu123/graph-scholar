from pathlib import Path

from app.core.config import get_settings
from app.services.ocr_landingai import extract_pdf


def test_ocr_mock(tmp_path, monkeypatch):
    monkeypatch.setenv("LANDINGAI_MOCK", "true")
    monkeypatch.setenv("EXTRACTED_DIR", str(tmp_path / "extracted"))
    get_settings.cache_clear()
    (tmp_path / "sample.pdf").write_bytes(b"%PDF-1.4 mock")
    payload = extract_pdf(tmp_path / "sample.pdf", "doc-123")
    assert "pages" in payload
    assert payload["full_text"]
