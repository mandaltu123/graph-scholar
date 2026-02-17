from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List

import requests

from app.core.config import get_settings


@dataclass
class OcrPage:
    page_num: int
    text: str
    blocks: List[Dict[str, Any]]


def _mock_ocr(doc_id: str) -> Dict[str, Any]:
    seed = hashlib.md5(doc_id.encode("utf-8")).hexdigest()[:8]
    pages: List[Dict[str, Any]] = []
    for idx in range(1, 4):
        pages.append(
            {
                "page_num": idx,
                "text": (
                    "LandingAI mock OCR output. "
                    "Set LANDINGAI_MOCK=false for real OCR.\n"
                    f"Seed: {seed}\n"
                    f"Page {idx} sample content for testing."
                ),
                "blocks": [],
            }
        )
    full_text = "\n\n".join(page["text"] for page in pages)
    return {"pages": pages, "full_text": full_text}


def _persist_extraction(doc_id: str, payload: Dict[str, Any]) -> None:
    settings = get_settings()
    extracted_dir = Path(settings.extracted_dir)
    extracted_dir.mkdir(parents=True, exist_ok=True)
    json_path = extracted_dir / f"{doc_id}.json"
    text_path = extracted_dir / f"{doc_id}.txt"
    json_path.write_text(json.dumps(payload, ensure_ascii=True, indent=2), encoding="utf-8")
    text_path.write_text(payload.get("full_text", ""), encoding="utf-8")


def extract_pdf(file_path: Path, doc_id: str) -> Dict[str, Any]:
    settings = get_settings()
    if settings.landingai_mock:
        payload = _mock_ocr(doc_id)
        _persist_extraction(doc_id, payload)
        return payload

    if not settings.landingai_api_key or not settings.landingai_endpoint:
        raise RuntimeError(
            "LandingAI credentials missing. Set LANDINGAI_API_KEY and LANDINGAI_ENDPOINT."
        )

    headers = {"Authorization": f"Bearer {settings.landingai_api_key}"}
    with file_path.open("rb") as fh:
        response = requests.post(
            settings.landingai_endpoint,
            headers=headers,
            files={"document": fh},
            timeout=120,
        )
    if response.status_code >= 400:
        raise RuntimeError(
            f"LandingAI OCR failed: {response.status_code} {response.text}"
        )

    data = response.json()
    raw_pages = data.get("pages")
    if raw_pages is None:
        raw_pages = data.get("data", {}).get("pages")
    if raw_pages is None:
        raw_pages = data.get("document", {}).get("pages")
    def _clean_markdown(text: str) -> str:
        cleaned = text.replace("<::", "").replace("::>", "")
        cleaned = cleaned.replace("<a id='", "").replace("'></a>", "")
        cleaned = cleaned.replace("\n\n", "\n")
        return cleaned.strip()

    pages: List[Dict[str, Any]] = []
    for idx, page in enumerate(raw_pages or [], start=1):
        pages.append(
            {
                "page_num": int(page.get("page_number") or page.get("page_num") or idx),
                "text": page.get("text") or page.get("content") or "",
                "blocks": page.get("blocks", []) or page.get("lines", []) or [],
            }
        )
    if not pages:
        chunks = data.get("chunks") or []
        if chunks:
            page_map: Dict[int, List[str]] = {}
            for chunk in chunks:
                grounding = chunk.get("grounding", {})
                page_idx = grounding.get("page", 0)
                page_num = int(page_idx) + 1
                page_map.setdefault(page_num, []).append(
                    _clean_markdown(chunk.get("markdown", ""))
                )
            for page_num, texts in sorted(page_map.items()):
                pages.append(
                    {
                        "page_num": page_num,
                        "text": "\n".join([t for t in texts if t]),
                        "blocks": chunks,
                    }
                )
    if not pages and data.get("markdown"):
        pages = [
            {"page_num": 1, "text": _clean_markdown(data.get("markdown", "")), "blocks": []}
        ]
    if not pages and data.get("text"):
        pages = [{"page_num": 1, "text": data.get("text", ""), "blocks": []}]
    full_text = "\n\n".join(page.get("text", "") for page in pages)
    payload = {"pages": pages, "full_text": full_text, "raw": data}
    _persist_extraction(doc_id, payload)
    return payload
