"""
Natural-language intent detection for the Retail Sales & Inventory Copilot.

Design:
1. Normalize the manager's question.
2. Use deterministic phrase rules for clear questions.
3. Return AMBIGUOUS when the question is unclear.
4. Return CANNOT_ANSWER for clearly unsupported questions.
5. Gemini can later handle genuinely ambiguous questions.

This module does NOT calculate business numbers.
Business calculations remain in analytics.py.
"""

import re
from dataclasses import dataclass
from enum import Enum
from typing import Optional

from intent import Intent


class DetectionStatus(str, Enum):
    """
    Status of the intent detection result.
    """

    CLEAR = "clear"
    AMBIGUOUS = "ambiguous"
    UNSUPPORTED = "unsupported"


@dataclass
class IntentResult:
    """
    Result returned by the intent detector.
    """

    intent: Intent
    confidence: str
    status: DetectionStatus
    matched_rule: Optional[str] = None


# ---------------------------------------------------------------------------
# Supported intent phrase rules
# ---------------------------------------------------------------------------

INTENT_RULES = {

    Intent.STOCKOUT_RISK: [
        "running out",
        "run out",
        "stock out",
        "stockout",
        "stock-out",
        "low stock",
        "low inventory",
        "need to reorder",
        "what do i need to reorder",
        "reorder",
        "shortage",
        "likely to run out",
    ],

    Intent.OVERSTOCK: [
        "overstock",
        "overstocked",
        "excess stock",
        "excess inventory",
        "too much inventory",
        "too much stock",
        "excessive inventory",
        "inventory is too high",
        "stock is too high",
        "more stock than needed",
    ],

    Intent.NON_MOVING: [
        "not moving",
        "non moving",
        "non-moving",
        "dead stock",
        "not selling",
        "no recent sales",
        "sitting unsold",
        "unsold inventory",
        "unsold stock",
    ],

    Intent.SALES_SPIKE: [
        "sales spike",
        "sales spikes",
        "spike in sales",
        "spikes in sales",
        "sales increased",
        "sales increase",
        "sales increases",
        "selling faster",
        "selling much faster",
        "unusually high sales",
        "recent sales increase",
    ],

    Intent.SALES_DROP: [
        "sales drop",
        "sales drops",
        "drop in sales",
        "drops in sales",
        "sales declined",
        "sales decline",
        "sales decreases",
        "sales decreased",
        "sales falling",
        "falling sales",
        "declining sales",
        "selling less",
        "selling less than usual",
    ],

    Intent.PRODUCT_PERFORMANCE: [
        "how did",
        "how is",
        "how are",
        "performance of",
        "performing",
        "sales of",
        "how many units",
        "units sold",
        "revenue of",
        "product performance",
    ],

    Intent.GENERAL_INVENTORY: [
        "inventory overview",
        "inventory summary",
        "inventory situation",
        "inventory status",
        "stock summary",
        "stock overview",
        "inventory doing",
        "stock doing",
        "overall inventory",
        "overall stock",
    ],
}


# ---------------------------------------------------------------------------
# Clearly unsupported questions
# ---------------------------------------------------------------------------

UNSUPPORTED_PHRASES = [
    "next year",
    "next month forecast",
    "future sales",
    "predict sales",
    "forecast sales",
    "customer satisfaction",
    "customer opinion",
    "customers dislike",
    "competitor",
    "competitors",
    "employee",
    "employees",
    "profit forecast",
    "market share",
    "social media",
]


# ---------------------------------------------------------------------------
# Text normalization
# ---------------------------------------------------------------------------

def normalize_question(question: str) -> str:
    """
    Normalize a manager question for matching.

    Args:
        question: Raw manager question.

    Returns:
        Normalized lowercase question.

    Raises:
        ValueError: If the question is empty or not a string.
    """

    if not isinstance(question, str):
        raise ValueError("Question must be a string.")

    normalized = question.strip().lower()

    if not normalized:
        raise ValueError("Question cannot be empty.")

    normalized = re.sub(r"\s+", " ", normalized)

    return normalized


# ---------------------------------------------------------------------------
# Matching helpers
# ---------------------------------------------------------------------------

def _find_matching_intents(question: str):
    """
    Find all supported intents matching the question.

    Returns:
        list[tuple[Intent, str]]
    """

    matches = []

    for intent, phrases in INTENT_RULES.items():

        for phrase in phrases:

            if phrase in question:
                matches.append((intent, phrase))
                break

    return matches


def _find_unsupported_phrase(question: str) -> Optional[str]:
    """
    Find a clearly unsupported topic.

    Returns:
        Matching phrase or None.
    """

    for phrase in UNSUPPORTED_PHRASES:

        if phrase in question:
            return phrase

    return None


# ---------------------------------------------------------------------------
# Main intent detector
# ---------------------------------------------------------------------------

def detect_intent(question: str) -> IntentResult:
    """
    Detect the intent of a manager question.

    Behavior:
    - Clear supported question → CLEAR
    - Multiple conflicting intents → AMBIGUOUS
    - No supported intent and no unsupported topic → AMBIGUOUS
    - Clearly unsupported topic → UNSUPPORTED / CANNOT_ANSWER

    Args:
        question: Manager's natural-language question.

    Returns:
        IntentResult
    """

    normalized = normalize_question(question)

    # ---------------------------------------------------------------
    # 1. Check clearly unsupported questions first.
    # ---------------------------------------------------------------

    unsupported_phrase = _find_unsupported_phrase(normalized)

    if unsupported_phrase:

        return IntentResult(
            intent=Intent.CANNOT_ANSWER,
            confidence="high",
            status=DetectionStatus.UNSUPPORTED,
            matched_rule=unsupported_phrase,
        )

    # ---------------------------------------------------------------
    # 2. Find supported intent matches.
    # ---------------------------------------------------------------

    matches = _find_matching_intents(normalized)

    # ---------------------------------------------------------------
    # 3. Nothing matched → ambiguous.
    # ---------------------------------------------------------------

    if not matches:

        return IntentResult(
            intent=Intent.CANNOT_ANSWER,
            confidence="low",
            status=DetectionStatus.AMBIGUOUS,
            matched_rule=None,
        )

    # ---------------------------------------------------------------
    # 4. Check for conflicting intents.
    # ---------------------------------------------------------------

    unique_intents = list(
        dict.fromkeys(
            intent
            for intent, _ in matches
        )
    )

    if len(unique_intents) > 1:

        return IntentResult(
            intent=Intent.CANNOT_ANSWER,
            confidence="low",
            status=DetectionStatus.AMBIGUOUS,
            matched_rule="multiple_intents",
        )

    # ---------------------------------------------------------------
    # 5. Clear supported intent.
    # ---------------------------------------------------------------

    intent, matched_phrase = matches[0]

    return IntentResult(
        intent=intent,
        confidence="high",
        status=DetectionStatus.CLEAR,
        matched_rule=matched_phrase,
    )


# ---------------------------------------------------------------------------
# Development test
# ---------------------------------------------------------------------------

if __name__ == "__main__":

    test_questions = [

        # Clear supported questions
        "What products are running out?",
        "Which products are overstocked?",
        "Show me dead stock.",
        "How did Wheat Flour 5kg perform?",
        "Which products have sales spikes?",
        "Which products have sales drops?",
        "Give me an inventory overview.",

        # Clearly unsupported
        "What will our sales be next year?",
        "What are our competitors doing?",

        # Ambiguous
        "What happened?",
        "Tell me about sales.",
    ]

    print("=" * 70)
    print("RETAIL COPILOT - INTENT DETECTOR TEST")
    print("=" * 70)

    for question in test_questions:

        result = detect_intent(question)

        print()
        print(f"Question   : {question}")
        print(f"Intent     : {result.intent.value}")
        print(f"Confidence : {result.confidence}")
        print(f"Status     : {result.status.value}")
        print(f"Rule       : {result.matched_rule}")

    print()
    print("=" * 70)
    print("INTENT DETECTOR TEST COMPLETE")
    print("=" * 70)