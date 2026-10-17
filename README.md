# Iqvora

Free-cloud educational AI tutor for ZIMSEC and Cambridge students.

**Stack:** FastAPI (Render Free) · Supabase (Postgres + Storage) ·
Qdrant Cloud (vector search) · Gemini API (generation) ·
BGE-small embeddings · Tesseract OCR.

## Project structure

```
iqvora/
├── app/
│   ├── __init__.py
│   ├── main.py            # FastAPI app, endpoints, CORS
│   ├── config.py          # pydantic-settings
│   ├── ai.py              # Gemini client (lazy)
│   ├── database.py        # Supabase client (lazy)
│   ├── rag/
│   │   ├── embeddings.py  # BGE-small via sentence-transformers
│   │   ├── qdrant_store.py# collection, upsert, delete-by-source
│   │   ├── ingest.py      # PDF -> chunks -> embeddings -> Qdrant (+ OCR)
│   │   └── retriever.py   # question -> vectors -> top chunks
│   └── services/
│       ├── chat.py        # RAG answer + chat history persistence
│       └── documents.py   # upload validation + ingestion pipeline
├── supabase/
│   └── schema.sql         # run once in the Supabase SQL Editor
├── requirements.txt
├── Dockerfile
├── render.yaml
├── .env.example
└── .gitignore
```

## One-time setup

1. **Supabase** — create a project, open the SQL Editor, and run
   `supabase/schema.sql`. Optionally create a private storage bucket
   called `iqvora-documents`.
2. **Qdrant Cloud** — create a free cluster and copy its URL and API key.
3. **Gemini** — create an API key in Google AI Studio.
4. **Render** — push this repo to GitHub, create a Web Service from it
   (Render reads `render.yaml`), and set the environment variables:

   | Variable | Value |
   |---|---|
   | `GEMINI_API_KEY` | your Gemini key |
   | `GEMINI_MODEL` | `gemini-2.5-flash` |
   | `SUPABASE_URL` | `https://YOUR_PROJECT.supabase.co` |
   | `SUPABASE_KEY` | your **service_role** key (server-side only) |
   | `QDRANT_URL` | your Qdrant cluster URL |
   | `QDRANT_API_KEY` | your Qdrant API key |
   | `QDRANT_COLLECTION` | `iqvora_documents` |
   | `EMBEDDING_MODEL` | `BAAI/bge-small-en-v1.5` |
   | `EMBEDDING_DIM` | `384` |
   | `MAX_UPLOAD_MB` | `20` |
   | `CORS_ORIGINS` | `*` for now, restrict later |

   Never commit secrets — `.env` is gitignored.

## Local development

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # fill in your values
uvicorn app.main:app --reload
```

Interactive docs: http://localhost:8000/docs

## Endpoints

| Method | Path | Purpose |
|---|---|---|
| GET | `/` | service info |
| GET | `/health` | health + which backends are configured |
| POST | `/api/chat` | ask a question (`student_id`, `question`) |
| POST | `/api/documents/upload` | upload + index a PDF (multipart form) |

## Notes and current limitations

- PDF ingestion runs inside the request. On the Render free tier, very
  large textbooks may hit request timeouts — move ingestion to a
  background worker before scaling up.
- `student_id` is currently free text; authentication and authorization
  are the next milestone before real students use it.
- Re-uploading a file with the same name replaces its old chunks in
  Qdrant (delete-by-source before upsert).
- Scanned PDFs are handled by Tesseract OCR (installed in the Docker
  image); handwriting quality varies.
