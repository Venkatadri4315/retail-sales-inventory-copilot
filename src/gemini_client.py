"""
Gemini client for the Retail Sales & Inventory Copilot.

Gemini's role:
- Explain deterministic evidence.
- Produce a concise manager-friendly answer.
- Never invent numbers.
- Never access the database directly.

The Gemini API key is read from GEMINI_API_KEY.
"""

import json
import os
from typing import Any, Dict

from google import genai


MODEL_NAME = "gemini-3.6-flash"


SYSTEM_INSTRUCTION = """
You are the explanation layer of a retail sales and inventory copilot.

Your job is to explain ONLY the evidence provided by the application.

STRICT RULES:
1. Never invent numbers, products, stores, dates, causes, or facts.
2. Use only information present in the provided evidence.
3. Python and SQLite have already calculated the business metrics.
4. Do not recalculate business metrics.
5. Every important numerical claim must be traceable to the evidence.
6. Clearly distinguish facts from recommendations.
7. A sales spike or drop does NOT prove its cause.
8. If a recorded business event supports a possible explanation,
   say "A recorded event may be related" rather than claiming causation.
9. If the evidence is empty or insufficient, say that the available
   data cannot reliably answer the question.
10. Keep the answer concise and useful for a retail manager.

Preferred response structure:

Answer:
- Direct answer to the manager's question.

Key evidence:
- Important numbers from the supplied evidence.

Recommended action:
- One practical action supported by the evidence.

Caveat:
- Mention an important limitation when necessary.
"""


def get_client() -> genai.Client:
    """
    Create and return a Gemini client.

    Raises:
        RuntimeError:
            If GEMINI_API_KEY is not configured.
    """

    api_key = os.getenv("GEMINI_API_KEY")

    if not api_key:
        raise RuntimeError(
            "GEMINI_API_KEY is not configured. "
            "Set the environment variable before using Gemini."
        )

    return genai.Client(api_key=api_key)


def _build_prompt(
    question: str,
    evidence_package: Dict[str, Any],
) -> str:
    """
    Build a grounded prompt from the manager question
    and deterministic evidence.
    """

    evidence_json = json.dumps(
        evidence_package,
        indent=2,
        ensure_ascii=False,
        default=str,
    )

    return f"""
Manager question:
{question}

Deterministic evidence from the retail database:
{evidence_json}

Using ONLY the evidence above, answer the manager's question.
"""


def generate_answer(
    question: str,
    evidence_package: Dict[str, Any],
) -> str:
    """
    Generate a grounded manager-facing answer using Gemini.

    Gemini receives structured evidence only.
    """

    if not isinstance(question, str) or not question.strip():
        raise ValueError("Question cannot be empty.")

    if not isinstance(evidence_package, dict):
        raise ValueError("Evidence package must be a dictionary.")

    if not evidence_package.get("answerable", False):
        return (
            "I cannot answer this reliably from the available "
            "retail data."
        )

    client = get_client()

    prompt = _build_prompt(
        question,
        evidence_package,
    )

    interaction = client.interactions.create(
        model=MODEL_NAME,
        input=prompt,
        system_instruction=SYSTEM_INSTRUCTION,
    )

    text = getattr(interaction, "output_text", None)

    if not text:
        raise RuntimeError(
            "Gemini returned an empty response."
        )

    return text.strip()


if __name__ == "__main__":

    print("=" * 70)
    print("RETAIL COPILOT - GEMINI CLIENT")
    print("=" * 70)

    api_key_configured = bool(
        os.getenv("GEMINI_API_KEY")
    )

    print()
    print(
        "GEMINI_API_KEY configured:",
        api_key_configured,
    )

    print(
        "Gemini model:",
        MODEL_NAME,
    )

    print()
    print(
        "The API key is intentionally not printed."
    )

    print("=" * 70)