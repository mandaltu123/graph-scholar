from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional

from app.core.config import get_settings


def _now() -> str:
    return datetime.utcnow().isoformat()


class DocStore:
    def __init__(self) -> None:
        settings = get_settings()
        self.index_path = Path(settings.doc_index_file)
        self.index_path.parent.mkdir(parents=True, exist_ok=True)

    def _load(self) -> Dict[str, dict]:
        if not self.index_path.exists():
            return {}
        return json.loads(self.index_path.read_text(encoding="utf-8"))

    def _save(self, data: Dict[str, dict]) -> None:
        self.index_path.write_text(
            json.dumps(data, ensure_ascii=True, indent=2), encoding="utf-8"
        )

    def create(self, doc_id: str, filename: str) -> dict:
        data = self._load()
        entry = {
            "doc_id": doc_id,
            "filename": filename,
            "status": "Processing",
            "chunk_count": 0,
            "embedded": False,
            "created_at": _now(),
            "updated_at": _now(),
            "embedding_model": None,
            "error": None,
        }
        data[doc_id] = entry
        self._save(data)
        return entry

    def update(self, doc_id: str, **updates: Optional[object]) -> dict:
        data = self._load()
        entry = data.get(doc_id, {"doc_id": doc_id})
        entry.update(updates)
        entry["updated_at"] = _now()
        data[doc_id] = entry
        self._save(data)
        return entry

    def get(self, doc_id: str) -> Optional[dict]:
        return self._load().get(doc_id)

    def list(self) -> Dict[str, dict]:
        return self._load()
