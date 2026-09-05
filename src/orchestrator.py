"""
Orchestrator for the Retail Sales & Inventory Copilot.

Responsibilities:
1. Detect the manager's intent.
2. Route the intent to deterministic analytics.
3. Build a grounded evidence package.
4. Return structured evidence for the Gemini explanation layer.

Gemini does NOT access the database directly.
Gemini will later explain only the evidence produced here.
"""

from typing import Any, Dict

from src.intent import Intent
from src.intent_detector import detect_intent, DetectionStatus
from src import analytics
from src.evidence import build_evidence


def handle_question(question: str) -> Dict[str, Any]:
    """
    Process a manager question through:

    Question
        -> Intent Detection
        -> Deterministic Analytics
        -> Evidence Builder

    Returns:
        A structured result containing grounded evidence.
    """

    # ---------------------------------------------------------------
    # Step 1: Detect intent
    # ---------------------------------------------------------------

    detection = detect_intent(question)

    # ---------------------------------------------------------------
    # Step 2: Handle unsupported or ambiguous questions
    # ---------------------------------------------------------------

    if detection.status != DetectionStatus.CLEAR:

        evidence_package = build_evidence(
            intent=detection.intent,
            question=question,
            analytics_result=[],
        )

        return {
            "question": question,
            "intent": detection.intent.value,
            "status": detection.status.value,
            "confidence": detection.confidence,
            "matched_rule": detection.matched_rule,
            "evidence": evidence_package,
        }

    # ---------------------------------------------------------------
    # Step 3: Route clear intents to deterministic analytics
    # ---------------------------------------------------------------

    if detection.intent == Intent.STOCKOUT_RISK:

        analytics_result = analytics.get_stockout_risks()

    elif detection.intent == Intent.OVERSTOCK:

        analytics_result = analytics.get_overstock_items()

    elif detection.intent == Intent.NON_MOVING:

        analytics_result = analytics.get_non_moving_items()

    elif detection.intent == Intent.SALES_SPIKE:

        analytics_result = analytics.get_sales_spikes()

    elif detection.intent == Intent.SALES_DROP:

        analytics_result = analytics.get_sales_drops()

    elif detection.intent == Intent.PRODUCT_PERFORMANCE:

        analytics_result = analytics.get_product_performance()

    elif detection.intent == Intent.GENERAL_INVENTORY:

        analytics_result = {
            "stockout_risks": analytics.get_stockout_risks(limit=10),
            "overstock_items": analytics.get_overstock_items(limit=10),
            "non_moving_items": analytics.get_non_moving_items(limit=10),
        }

    else:

        evidence_package = build_evidence(
            intent=Intent.CANNOT_ANSWER,
            question=question,
            analytics_result=[],
        )

        return {
            "question": question,
            "intent": Intent.CANNOT_ANSWER.value,
            "status": "unsupported",
            "confidence": "high",
            "matched_rule": None,
            "evidence": evidence_package,
        }

    # ---------------------------------------------------------------
    # Step 4: Build grounded evidence package
    # ---------------------------------------------------------------

    evidence_package = build_evidence(
        intent=detection.intent,
        question=question,
        analytics_result=analytics_result,
    )

    # ---------------------------------------------------------------
    # Step 5: Return complete structured result
    # ---------------------------------------------------------------

    return {
        "question": question,
        "intent": detection.intent.value,
        "status": detection.status.value,
        "confidence": detection.confidence,
        "matched_rule": detection.matched_rule,
        "evidence": evidence_package,
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
    print("EVIDENCE PACKAGE")
    print("-" * 70)

    evidence_package = result["evidence"]

    print(f"Answerable : {evidence_package.get('answerable')}")
    print()
    print("Calculation rule:")
    print(evidence_package.get("calculation_rule"))

    print()
    print("Recommendation basis:")
    print(evidence_package.get("recommendation_basis"))

    print()
    print("Assumptions:")

    for assumption in evidence_package.get("assumptions", []):
        print(f"- {assumption}")

    print()
    print("Analytics evidence:")

    analytics_evidence = evidence_package.get("evidence")

    if isinstance(analytics_evidence, list):

        print(f"Records returned: {len(analytics_evidence)}")

        for item in analytics_evidence[:5]:
            print(item)

    elif isinstance(analytics_evidence, dict):

        for key, value in analytics_evidence.items():

            print(f"{key}: {len(value)} records")

            for item in value[:2]:
                print(f"  {item}")

    else:
        print(analytics_evidence)

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