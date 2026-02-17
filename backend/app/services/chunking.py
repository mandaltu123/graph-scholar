from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any, Dict, List


@dataclass
class Chunk:
    chunk_id: str
    text: str
    page_num: int
    chunk_index: int
    metadata: Dict[str, Any]


def _split_into_sections(text: str) -> List[str]:
    lines = [ln.strip() for ln in text.splitlines()]
    sections: List[str] = []
    buffer: List[str] = []
    heading_pattern = re.compile(r"^(\d+(\.\d+)*\s+)?[A-Z][A-Za-z0-9\- ,]{3,}$")
    for line in lines:
        if heading_pattern.match(line) and buffer:
            sections.append("\n".join(buffer).strip())
            buffer = [line]
            continue
        buffer.append(line)
    if buffer:
        sections.append("\n".join(buffer).strip())
    return [sec for sec in sections if sec]


def chunk_pages(
    pages: List[Dict[str, Any]],
    doc_id: str,
    chunk_size_chars: int,
    overlap_chars: int,
) -> List[Chunk]:
    if overlap_chars >= chunk_size_chars:
        raise ValueError("overlap_chars must be smaller than chunk_size_chars.")

    chunks: List[Chunk] = []
    chunk_index = 0
    for page in pages:
        page_num = int(page.get("page_num", 0))
        text = (page.get("text") or "").strip()
        if not text:
            continue
        sections = _split_into_sections(text)
        for section in sections:
            start = 0
            while start < len(section):
                end = min(len(section), start + chunk_size_chars)
                slice_text = section[start:end].strip()
                if slice_text:
                    chunk_ref = f"p{page_num}-c{chunk_index}"
                    chunk_id = f"{doc_id}:{chunk_ref}"
                    metadata = {
                        "doc_id": doc_id,
                        "page_num": page_num,
                        "chunk_index": chunk_index,
                        "chunk_ref": chunk_ref,
                        "source": "landingai",
                        "offset_start": start,
                        "offset_end": end,
                    }
                    chunks.append(
                        Chunk(
                            chunk_id=chunk_id,
                            text=slice_text,
                            page_num=page_num,
                            chunk_index=chunk_index,
                            metadata=metadata,
                        )
                    )
                    chunk_index += 1
                if end == len(section):
                    break
                start = max(0, end - overlap_chars)
    return chunks
