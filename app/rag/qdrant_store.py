from functools import lru_cache
from uuid import NAMESPACE_URL, uuid5

from qdrant_client import QdrantClient
from qdrant_client.models import (
    Distance,
    FieldCondition,
    Filter,
    MatchValue,
    PointStruct,
    VectorParams,
)

from ..config import settings


@lru_cache(maxsize=1)
def get_client() -> QdrantClient:
    if not settings.qdrant_url:
        raise RuntimeError("QDRANT_URL is not configured.")

    return QdrantClient(
        url=settings.qdrant_url,
        api_key=settings.qdrant_api_key or None,
    )


def ensure_collection() -> None:
    client = get_client()

    names = {
        collection.name
        for collection in client.get_collections().collections
    }

    if settings.qdrant_collection not in names:
        client.create_collection(
            collection_name=settings.qdrant_collection,
            vectors_config=VectorParams(
                size=settings.embedding_dim,
                distance=Distance.COSINE,
            ),
        )


def make_point_id(
    source: str,
    page: int,
    chunk_index: int,
) -> str:
    value = f"{source}:{page}:{chunk_index}"

    return str(uuid5(NAMESPACE_URL, value))


def delete_by_source(source: str) -> None:
    """Remove all chunks previously ingested from this source file.

    Prevents stale chunks from surviving when a file is re-uploaded
    with the same name but different content.
    """
    client = get_client()
    ensure_collection()

    client.delete(
        collection_name=settings.qdrant_collection,
        points_selector=Filter(
            must=[
                FieldCondition(
                    key="source",
                    match=MatchValue(value=source),
                )
            ]
        ),
    )


def add_chunks(chunks: list[dict]) -> None:
    ensure_collection()

    points = []

    for chunk in chunks:
        point_id = make_point_id(
            chunk["source"],
            chunk["page"],
            chunk["chunk_index"],
        )

        points.append(
            PointStruct(
                id=point_id,
                vector=chunk["vector"],
                payload={
                    "text": chunk["text"],
                    "source": chunk["source"],
                    "page": chunk["page"],
                    "subject": chunk.get("subject"),
                    "topic": chunk.get("topic"),
                    "grade_level": chunk.get("grade_level"),
                    "curriculum": chunk.get(
                        "curriculum",
                        "ZIMSEC",
                    ),
                    "document_type": chunk.get(
                        "document_type"
                    ),
                },
            )
        )

    if points:
        get_client().upsert(
            collection_name=settings.qdrant_collection,
            points=points,
        )


def search(vector: list[float], limit: int = 5) -> list:
    ensure_collection()

    result = get_client().query_points(
        collection_name=settings.qdrant_collection,
        query=vector,
        limit=limit,
        with_payload=True,
    )

    return result.points
