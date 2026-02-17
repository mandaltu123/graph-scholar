from __future__ import annotations

import os
from typing import Optional

from fastapi import APIRouter
from pydantic import BaseModel
from app.core.config import get_settings, REPO_DIR

router = APIRouter()


class HealthResponse(BaseModel):
    status: str


class DebugConfigResponse(BaseModel):
    landingai_mock: bool
    landingai_endpoint: Optional[str]
    env_file: str
    env_file_exists: bool


@router.get("/health", response_model=HealthResponse)
async def health() -> HealthResponse:
    return HealthResponse(status="ok")


@router.get("/api/debug/config", response_model=DebugConfigResponse)
async def debug_config() -> DebugConfigResponse:
    settings = get_settings()
    env_file = os.environ.get("ENV_FILE", str(REPO_DIR / "backend" / ".env"))
    return DebugConfigResponse(
        landingai_mock=settings.landingai_mock,
        landingai_endpoint=settings.landingai_endpoint,
        env_file=env_file,
        env_file_exists=os.path.exists(env_file),
    )
