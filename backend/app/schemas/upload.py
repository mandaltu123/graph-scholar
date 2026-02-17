from __future__ import annotations

from pydantic import BaseModel


class UploadResponse(BaseModel):
    doc_id: str
    filename: str
    status: str
