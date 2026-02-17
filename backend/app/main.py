from __future__ import annotations

import logging
import time
import uuid
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.routes_chat import router as chat_router
from app.api.routes_docs import router as docs_router
from app.api.routes_health import router as health_router
from app.api.routes_upload import router as upload_router
from app.core.config import get_settings
from app.core.logging import setup_logging


def create_app() -> FastAPI:
    setup_logging()
    settings = get_settings()
    app = FastAPI(title=settings.app_name)
    logger = logging.getLogger("scholargraph")

    app.add_middleware(
        CORSMiddleware,
        allow_origins=[origin.strip() for origin in settings.cors_origins.split(",")],
        allow_origin_regex=".*",
        allow_credentials=False,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.middleware("http")
    async def request_id_middleware(request: Request, call_next):
        request_id = request.headers.get(settings.request_id_header, str(uuid.uuid4()))
        start = time.time()
        response = await call_next(request)
        duration_ms = int((time.time() - start) * 1000)
        response.headers[settings.request_id_header] = request_id
        logger.info(
            "request_id=%s method=%s path=%s status=%s duration_ms=%s",
            request_id,
            request.method,
            request.url.path,
            response.status_code,
            duration_ms,
        )
        return response

    @app.exception_handler(Exception)
    async def unhandled_exception_handler(request: Request, exc: Exception):
        logger.exception("Unhandled error")
        return JSONResponse(
            status_code=500,
            content={"detail": "Unexpected server error."},
        )

    app.include_router(health_router)
    app.include_router(upload_router, prefix="/api")
    app.include_router(chat_router, prefix="/api")
    app.include_router(docs_router, prefix="/api")
    return app


app = create_app()
