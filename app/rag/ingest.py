import io
from pathlib import Path

import pytesseract
from langchain_text_splitters import (
    RecursiveCharacterTextSplitter,
)
from PIL import Image
from pypdf import PdfReader

from .embeddings import embed_texts
from .qdrant_store import add_chunks, delete_by_source


def _ocr_pdf_page(path: str, page_number: int) -> str:
    """Render one page of a scanned PDF with PyMuPDF and OCR it."""
    import fitz  # PyMuPDF

    doc = fitz.open(path)

    try:
        page = doc[page_number - 1]
        pixmap = page.get_pixmap(dpi=200)
        image = Image.open(io.BytesIO(pixmap.tobytes("png")))

        return pytesseract.image_to_string(image)

    finally:
        doc.close()


def extract_pdf(
    path: str,
    use_ocr: bool = True,
) -> list[dict]:

    reader = PdfReader(path)

    pages = []

    for page_number, page in enumerate(
        reader.pages,
        start=1,
    ):

        text = page.extract_text() or ""
        text = text.strip()

        if not text and use_ocr:
            try:
                text = _ocr_pdf_page(
                    path,
                    page_number,
                ).strip()
            except Exception:
                # OCR unavailable or failed: skip the page rather
                # than crash the whole upload.
                text = ""

        if not text:
            continue

        pages.append({
            "page": page_number,
            "text": text,
        })

    return pages


def ingest_pdf(
    path: str,
    subject: str | None = None,
    topic: str | None = None,
    grade_level: str | None = None,
    curriculum: str = "ZIMSEC",
    document_type: str = "notes",
) -> dict:

    source = Path(path).name

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=800,
        chunk_overlap=150,
        separators=[
            "\n\n",
            "\n",
            ". ",
            " ",
            "",
        ],
    )

    raw_chunks = []

    pages = extract_pdf(path)

    for page in pages:

        chunks = splitter.split_text(page["text"])

        for index, chunk in enumerate(chunks):

            raw_chunks.append({
                "text": chunk,
                "source": source,
                "page": page["page"],
                "chunk_index": index,
                "subject": subject,
                "topic": topic,
                "grade_level": grade_level,
                "curriculum": curriculum,
                "document_type": document_type,
            })

    if not raw_chunks:
        raise ValueError(
            "No text could be extracted from this PDF. "
            "If it is a scanned document, make sure OCR "
            "support is installed."
        )

    vectors = embed_texts(
        [item["text"] for item in raw_chunks]
    )

    for item, vector in zip(raw_chunks, vectors):
        item["vector"] = vector

    # Replace any previous version of this file before upserting,
    # so deleted or edited content never stays in the index.
    delete_by_source(source)
    add_chunks(raw_chunks)

    return {
        "chunks": len(raw_chunks),
        "pages": len(pages),
        "source": source,
    }
