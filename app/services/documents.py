import asyncio
import os
import tempfile

from fastapi import UploadFile

from ..config import settings
from ..database import get_supabase
from ..rag.ingest import ingest_pdf


async def save_and_ingest_pdf(
    file: UploadFile,
    subject: str | None = None,
    topic: str | None = None,
    grade_level: str | None = None,
    curriculum: str = "ZIMSEC",
    document_type: str = "notes",
) -> dict:

    if not file.filename:
        raise ValueError("Filename is required.")

    if not file.filename.lower().endswith(".pdf"):
        raise ValueError(
            "Only PDF files are supported."
        )

    data = await file.read()

    if not data.startswith(b"%PDF"):
        raise ValueError(
            "The uploaded file is not a valid PDF."
        )

    max_size = settings.max_upload_mb * 1024 * 1024

    if len(data) > max_size:
        raise ValueError(
            f"PDF is larger than "
            f"{settings.max_upload_mb} MB."
        )

    with tempfile.NamedTemporaryFile(
        suffix=".pdf",
        delete=False,
    ) as temp:

        temp.write(data)
        temp_path = temp.name

    try:

        # PDF extraction, OCR and embedding are all blocking
        # and CPU-heavy: keep them off the event loop.
        result = await asyncio.to_thread(
            ingest_pdf,
            temp_path,
            subject,
            topic,
            grade_level,
            curriculum,
            document_type,
        )

    finally:

        if os.path.exists(temp_path):
            os.remove(temp_path)

    supabase = get_supabase()

    if supabase:

        supabase.table("documents").insert({
            "filename": file.filename,
            "subject": subject,
            "topic": topic,
            "grade_level": grade_level,
            "curriculum": curriculum,
            "document_type": document_type,
            "status": "indexed",
        }).execute()

    return result
