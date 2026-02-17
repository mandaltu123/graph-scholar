from __future__ import annotations

import uuid
from pathlib import Path

from fastapi import APIRouter, File, HTTPException, UploadFile

from app.core.config import get_settings
from app.schemas.upload import UploadResponse
from app.services.doc_store import DocStore
from app.services.ingest import ingest_document

router = APIRouter()


@router.post("/upload", response_model=UploadResponse)
async def upload_pdf(file: UploadFile = File(...)) -> UploadResponse:
    if file.content_type not in {"application/pdf"}:
        raise HTTPException(status_code=400, detail="Only PDF files supported.")
    settings = get_settings()
    max_bytes = settings.max_upload_mb * 1024 * 1024
    contents = await file.read()
    if len(contents) > max_bytes:
        raise HTTPException(status_code=400, detail="File too large.")

    doc_id = str(uuid.uuid4())
    uploads_dir = Path(settings.uploads_dir)
    uploads_dir.mkdir(parents=True, exist_ok=True)
    pdf_path = uploads_dir / f"{doc_id}.pdf"
    pdf_path.write_bytes(contents)

    store = DocStore()
    store.create(doc_id, file.filename)

    try:
        ingest_document(doc_id, file.filename, pdf_path)
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail={"message": str(exc), "doc_id": doc_id},
        ) from exc

    return UploadResponse(doc_id=doc_id, filename=file.filename, status="Ready")


@router.post("/papers/upload")
async def legacy_upload_pdf(file: UploadFile = File(...)) -> dict:
    response = await upload_pdf(file)
    return {
        "paper_id": response.doc_id,
        "filename": response.filename,
        "status": response.status,
    }
