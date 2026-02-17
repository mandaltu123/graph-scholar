from __future__ import annotations

import json
import logging
from typing import Any, Dict, List

from app.services.llm_client import get_llm_client
from app.services.prompts import SYSTEM_VERIFY

logger = logging.getLogger(__name__)


def _extract_json(text: str) -> Dict[str, Any]:
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        start = text.find("{")
        end = text.rfind("}")
        if start >= 0 and end > start:
            try:
                return json.loads(text[start : end + 1])
            except json.JSONDecodeError:
                pass
    return {"grounded": False, "unsupported_claims": ["Invalid verifier response."], "fix_suggestion": ""}


def verify_answer(answer: str, context: str) -> Dict[str, Any]:
    client = get_llm_client()
    messages = [
        {"role": "system", "content": SYSTEM_VERIFY},
        {
            "role": "user",
            "content": f"Context:\n{context}\n\nAnswer:\n{answer}",
        },
    ]
    raw = client.chat(messages)
    data = _extract_json(raw)
    data.setdefault("grounded", False)
    data.setdefault("unsupported_claims", [])
    data.setdefault("fix_suggestion", "")
    return data


def heuristic_grounding(answer: str, chunk_ids: List[str]) -> Dict[str, Any]:
    missing = []
    if not chunk_ids:
        missing.append("No retrieved chunks.")
    if "[" not in answer or "]" not in answer:
        missing.append("Missing citations.")
    cited = []
    for chunk_id in chunk_ids:
        if chunk_id in answer:
            cited.append(chunk_id)
    if chunk_ids and not cited:
        missing.append("No valid chunk ids referenced.")
    return {"ok": len(missing) == 0, "notes": "; ".join(missing)}
