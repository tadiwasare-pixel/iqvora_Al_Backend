import asyncio

from fastapi import (
    FastAPI,
    File,
    Form,
    HTTPException,
    UploadFile,
)
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from .config import settings
from .services.chat import answer_question
from .services.documents import (
    save_and_ingest_pdf,
)


app = FastAPI(
    title=settings.app_name,
    version="2.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        origin.strip()
        for origin in settings.cors_origins.split(",")
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class ChatRequest(BaseModel):
    student_id: str = Field(min_length=1)
    question: str = Field(min_length=1)


@app.get("/")
def root():

    return {
        "app": "Iqvora",
        "version": "2.1.0",
        "status": "online",
    }


@app.get("/health")
def health():

    return {
        "status": "healthy",
        "app": "Iqvora",
        "version": "2.1.0",
        "configured": {
            "gemini": bool(settings.gemini_api_key),
            "supabase": bool(
                settings.supabase_url
                and settings.supabase_key
            ),
            "qdrant": bool(settings.qdrant_url),
        },
    }


@app.post("/api/chat")
async def chat(request: ChatRequest):

    question = request.question.strip()

    if not question:
        raise HTTPException(
            status_code=400,
            detail="Question cannot be empty.",
        )

    try:

        return await asyncio.to_thread(
            answer_question,
            request.student_id,
            question,
        )

    except Exception as error:

        raise HTTPException(
            status_code=500,
            detail=str(error),
        )


@app.post("/api/documents/upload")
async def upload_document(
    file: UploadFile = File(...),
    subject: str | None = Form(None),
    topic: str | None = Form(None),
    grade_level: str | None = Form(None),
    curriculum: str = Form("ZIMSEC"),
    document_type: str = Form("notes"),
):

    try:

        return await save_and_ingest_pdf(
            file=file,
            subject=subject,
            topic=topic,
            grade_level=grade_level,
            curriculum=curriculum,
            document_type=document_type,
        )

    except ValueError as error:

        raise HTTPException(
            status_code=400,
            detail=str(error),
        )

    except Exception as error:

        raise HTTPException(
            status_code=500,
            detail=str(error),
        )
