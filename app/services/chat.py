from ..ai import generate_answer
from ..database import get_supabase
from ..rag.retriever import retrieve


def answer_question(
    student_id: str,
    question: str,
) -> dict:

    documents = retrieve(question, limit=5)

    if documents:

        context_parts = []

        for document in documents:

            context_parts.append(
                f"""
Source: {document["source"]}
Page: {document["page"]}
Subject: {document.get("subject")}

Content:
{document["text"]}
"""
            )

        context = "\n\n".join(context_parts)

    else:

        context = (
            "No matching educational "
            "documents were found."
        )

    answer = generate_answer(question, context)

    sources = []

    for document in documents:

        sources.append({
            "source": document["source"],
            "page": document["page"],
            "score": document["score"],
        })

    supabase = get_supabase()

    if supabase:

        supabase.table(
            "chat_history"
        ).insert({
            "student_id": student_id,
            "question": question,
            "answer": answer,
        }).execute()

    return {
        "answer": answer,
        "sources": sources,
        "retrieval_count": len(documents),
    }
