from __future__ import annotations

import os
from functools import lru_cache
from pathlib import Path
from typing import Optional

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

REPO_DIR = Path(__file__).resolve().parents[3]
STORAGE_DIR = REPO_DIR / "storage"
DEFAULT_UPLOADS_DIR = STORAGE_DIR / "uploads"
DEFAULT_EXTRACTED_DIR = STORAGE_DIR / "extracted"
DEFAULT_CHROMA_DIR = STORAGE_DIR / "chroma"
DEFAULT_DOC_INDEX_FILE = STORAGE_DIR / "docs_index.json"


class Settings(BaseSettings):
    app_name: str = "ScholarGraph-RAG"
    env: str = Field("dev", env="APP_ENV")
    cors_origins: str = Field(
        "http://localhost:5173,http://127.0.0.1:5173", env="CORS_ORIGINS"
    )
    request_id_header: str = Field("X-Request-Id", env="REQUEST_ID_HEADER")
    log_level: str = Field("INFO", env="LOG_LEVEL")
    log_json: bool = Field(False, env="LOG_JSON")

    storage_dir: str = Field(str(STORAGE_DIR), env="STORAGE_DIR")
    uploads_dir: str = Field(str(DEFAULT_UPLOADS_DIR), env="UPLOADS_DIR")
    extracted_dir: str = Field(str(DEFAULT_EXTRACTED_DIR), env="EXTRACTED_DIR")
    chroma_persist_dir: str = Field(str(DEFAULT_CHROMA_DIR), env="CHROMA_PERSIST_DIR")
    doc_index_file: str = Field(str(DEFAULT_DOC_INDEX_FILE), env="DOC_INDEX_FILE")
    chroma_collection: str = Field("papers", env="CHROMA_COLLECTION")

    max_upload_mb: int = Field(50, env="MAX_UPLOAD_MB")

    landingai_api_key: Optional[str] = Field(None, env="LANDINGAI_API_KEY")
    landingai_endpoint: Optional[str] = Field(None, env="LANDINGAI_ENDPOINT")
    landingai_mock: bool = Field(True, env="LANDINGAI_MOCK")

    chunk_size_chars: int = Field(3200, env="CHUNK_SIZE_CHARS")
    chunk_overlap_chars: int = Field(320, env="CHUNK_OVERLAP_CHARS")

    embedding_model: str = Field(
        "sentence-transformers/all-MiniLM-L6-v2", env="EMBEDDING_MODEL"
    )

    llama_base_url: str = Field("http://localhost:11434/v1", env="LLAMA_BASE_URL")
    llama_model: str = Field("llama3.1", env="LLAMA_MODEL")
    llama_api_key: Optional[str] = Field(None, env="LLAMA_API_KEY")
    llm_timeout_sec: int = Field(60, env="LLM_TIMEOUT_SEC")
    llm_max_tokens: int = Field(512, env="LLM_MAX_TOKENS")
    llm_temperature: float = Field(0.2, env="LLM_TEMPERATURE")

    default_top_k: int = Field(5, env="DEFAULT_TOP_K")
    max_retries: int = Field(2, env="MAX_RETRIES")
    max_context_chars: int = Field(8000, env="MAX_CONTEXT_CHARS")
    session_history_max: int = Field(10, env="SESSION_HISTORY_MAX")

    model_config = SettingsConfigDict(
        env_file=os.environ.get("ENV_FILE", str((REPO_DIR / "backend" / ".env"))),
        case_sensitive=False,
        extra="ignore",
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()
