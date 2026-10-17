from .embeddings import embed_text
from .qdrant_store import search


def retrieve(
    question: str,
    limit: int = 5,
) -> list[dict]:

    vector = embed_text(question)

    results = search(vector, limit=limit)

    documents = []

    for result in results:
        payload = result.payload or {}

        documents.append({
            "text": payload.get("text", ""),
            "source": payload.get("source"),
            "page": payload.get("page"),
            "subject": payload.get("subject"),
            "topic": payload.get("topic"),
            "curriculum": payload.get("curriculum"),
            "document_type": payload.get(
                "document_type"
            ),
            "score": result.score,
        })

    return documents
