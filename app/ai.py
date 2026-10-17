from functools import lru_cache

from google import genai
from google.genai import types

from .config import settings


@lru_cache(maxsize=1)
def get_ai_client() -> genai.Client:
    if not settings.gemini_api_key:
        raise RuntimeError("GEMINI_API_KEY is not configured.")

    return genai.Client(api_key=settings.gemini_api_key)


SYSTEM_PROMPT = """
You are Iqvora, an educational AI tutor.

You help students studying ZIMSEC and Cambridge curricula.

Rules:

1. Use the supplied educational context when it is relevant.
2. Do not invent information and pretend it came from a source.
3. If the supplied context does not contain the answer, say so.
4. Explain difficult concepts step by step.
5. For mathematics, show calculations.
6. For science, explain the reasoning.
7. Adapt explanations to the student's level.
8. Encourage understanding rather than copying.
9. Keep answers clear and structured.
10. Never fabricate page numbers or document citations.

When sources are supplied, cite them like:

Source: Biology Form 4, page 42
"""


def generate_answer(
    question: str,
    context: str,
) -> str:

    client = get_ai_client()

    prompt = f"""
Educational context:

{context}

Student question:

{question}

Answer the student using the rules above.
"""

    response = client.models.generate_content(
        model=settings.gemini_model,
        contents=prompt,
        config=types.GenerateContentConfig(
            system_instruction=SYSTEM_PROMPT,
            temperature=0.2,
            max_output_tokens=1500,
        ),
    )

    return response.text or (
        "I couldn't generate an answer."
    )
