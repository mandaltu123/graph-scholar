from __future__ import annotations

import logging
from typing import Dict, List, Optional
from urllib.parse import urljoin

import requests

from app.core.config import get_settings

logger = logging.getLogger(__name__)


class LlamaClient:
    def __init__(self) -> None:
        self.settings = get_settings()

    def chat(
        self,
        messages: List[Dict[str, str]],
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
    ) -> str:
        temp = temperature if temperature is not None else self.settings.llm_temperature
        max_out = max_tokens if max_tokens is not None else self.settings.llm_max_tokens
        base_url = self.settings.llama_base_url.rstrip("/")
        payload = {
            "model": self.settings.llama_model,
            "messages": messages,
            "temperature": temp,
            "max_tokens": max_out,
        }

        if base_url.endswith("/v1"):
            url = urljoin(f"{base_url}/", "chat/completions")
            return self._request_openai_compat(url, payload)

        url = urljoin(f"{base_url}/", "api/chat")
        payload = {
            "model": self.settings.llama_model,
            "messages": messages,
            "stream": False,
            "options": {"temperature": temp, "num_predict": max_out},
        }
        return self._request_ollama(url, payload)

    def _request_openai_compat(self, url: str, payload: dict) -> str:
        headers = {}
        if self.settings.llama_api_key:
            headers["Authorization"] = f"Bearer {self.settings.llama_api_key}"
        try:
            resp = requests.post(
                url, json=payload, headers=headers, timeout=self.settings.llm_timeout_sec
            )
        except requests.exceptions.RequestException as exc:
            raise RuntimeError(
                f"Llama server request failed at {url}. Ensure server is running."
            ) from exc
        if resp.status_code >= 400:
            raise RuntimeError(f"Llama server error: {resp.status_code} {resp.text}")
        data = resp.json()
        return data.get("choices", [{}])[0].get("message", {}).get("content", "")

    def _request_ollama(self, url: str, payload: dict) -> str:
        try:
            resp = requests.post(
                url, json=payload, timeout=self.settings.llm_timeout_sec
            )
        except requests.exceptions.RequestException as exc:
            raise RuntimeError(
                f"Ollama request failed at {url}. Ensure Ollama is running."
            ) from exc
        if resp.status_code >= 400:
            raise RuntimeError(f"Ollama error: {resp.status_code} {resp.text}")
        data = resp.json()
        return data.get("message", {}).get("content", "")


def get_llm_client() -> LlamaClient:
    return LlamaClient()
