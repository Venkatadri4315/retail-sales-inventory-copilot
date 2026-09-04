"""
Orchestrator for the Retail Sales & Inventory Copilot.

Responsibilities:
1. Detect the manager's intent.
2. Route the intent to the correct deterministic analytics function.
3. Return structured evidence containing actual database numbers.

Gemini is NOT used here.
Gemini will later explain this evidence without inventing numbers.
"""

from typing import Any, Dict

from intent import Intent
from intent_detector import detect_intent, DetectionStatus
import analytics


def handle_question(question: str) -> Dict[str, Any]:
    """
    Process a manager question through intent detection
    and deterministic analytics.

    Returns a structured result that can later be passed
    to Gemini for explanation.
    """

    # Step 1: Detect intent
    detection = detect_intent(question)

    # Step 2: Handle unsupported or ambiguous questions
    if detection.status != DetectionStatus.CLEAR:
        return {
            "question": question,
            "intent": detection.intent.value,
            "status": detection.status.value,
            "confidence": detection.confidence,
            "matched_rule": detection.matched_rule,
            "evidence": [],
            "message": (
                "I cannot answer this reliably from the available "
                "retail data."
            ),
        }

    # Step 3: Route clear intents to deterministic analytics
    if detection.intent == Intent.STOCKOUT_RISK:
        evidence = analytics.get_stockout_risks()

    elif detection.intent == Intent.OVERSTOCK:
        evidence = analytics.get_overstock_items()

    elif detection.intent == Intent.NON_MOVING:
        evidence = analytics.get_non_moving_items()

    elif detection.intent == Intent.SALES_SPIKE:
        evidence = analytics.get_sales_spikes()

    elif detection.intent == Intent.SALES_DROP:
        evidence = analytics.get_sales_drops()

    elif detection.intent == Intent.PRODUCT_PERFORMANCE:
        evidence = analytics.get_product_performance()

    elif detection.intent == Intent.GENERAL_INVENTORY:
        evidence = {
            "stockout_risks": analytics.get_stockout_risks(limit=10),
            "overstock_items": analytics.get_overstock_items(limit=10),
            "non_moving_items": analytics.get_non_moving_items(limit=10),
        }

    else:
        return {
            "question": question,
            "intent": Intent.CANNOT_ANSWER.value,
            "status": "unsupported",
            "confidence": "high",
            "matched_rule": None,
            "evidence": [],
            "message": (
                "I cannot answer this reliably from the available "
                "retail data."
            ),
        }

    # Step 4: Return structured evidence
    return {
        "question": question,
        "intent": detection.intent.value,
        "status": detection.status.value,
        "confidence": detection.confidence,
        "matched_rule": detection.matched_rule,
        "evidence": evidence,
    }


def print_result(result: Dict[str, Any]) -> None:
    """
    Print an orchestrator result in a readable format.
    """

    print()
    print("=" * 70)
    print("RETAIL COPILOT - ORCHESTRATOR")
    print("=" * 70)

    print(f"Question   : {result['question']}")
    print(f"Intent     : {result['intent']}")
    print(f"Status     : {result['status']}")
    print(f"Confidence : {result['confidence']}")
    print(f"Rule       : {result['matched_rule']}")

    print()
    print("EVIDENCE")
    print("-" * 70)

    evidence = result["evidence"]

    if isinstance(evidence, list):

        print(f"Records returned: {len(evidence)}")

        for item in evidence[:5]:
            print(item)

    elif isinstance(evidence, dict):

        for key, value in evidence.items():
            print(f"{key}: {len(value)} records")

            for item in value[:2]:
                print(f"  {item}")

    else:
        print(evidence)

    if "message" in result:
        print()
        print("MESSAGE")
        print("-" * 70)
        print(result["message"])

    print("=" * 70)


if __name__ == "__main__":

    test_questions = [
        "What products are running out?",
        "Which products are overstocked?",
        "Show me dead stock.",
        "Which products have sales spikes?",
        "Which products have sales drops?",
        "Give me an inventory overview.",
        "What are our competitors doing?",
        "What happened?",
    ]

    for question in test_questions:

        result = handle_question(question)

        print_result(result)