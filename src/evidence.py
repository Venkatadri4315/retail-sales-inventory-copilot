"""
Evidence builder for the Retail Sales & Inventory Copilot.

Purpose:
- Convert deterministic analytics results into a consistent evidence package.
- Preserve the actual numbers calculated by analytics.py.
- Provide calculation rules and assumptions.
- Prepare safe, structured context for Gemini.

Gemini must explain this evidence.
It must NOT calculate or invent business numbers.
"""

from typing import Any, Dict, List

from src.intent import Intent

ANALYTIC_RULES = {
    Intent.STOCKOUT_RISK: {
        "title": "Stock-out Risk",
        "calculation": (
            "Current stock is compared with the reorder level and "
            "recent 14-day sales demand. Days of stock is estimated "
            "from current stock divided by average daily sales."
        ),
        "recommendation_basis": (
            "Prioritize replenishment when stock is at or below the "
            "reorder level and estimated days of stock are low."
        ),
    },

    Intent.OVERSTOCK: {
        "title": "Overstock",
        "calculation": (
            "Current stock is compared with target stock and recent "
            "30-day sales demand."
        ),
        "recommendation_basis": (
            "Consider reducing replenishment or increasing sell-through "
            "when inventory substantially exceeds target stock."
        ),
    },

    Intent.NON_MOVING: {
        "title": "Non-moving Stock",
        "calculation": (
            "Products with positive inventory and zero sales during "
            "the most recent 30-day period are identified."
        ),
        "recommendation_basis": (
            "Review pricing, placement, promotion, or replenishment "
            "decisions for inventory that is not moving."
        ),
    },

    Intent.PRODUCT_PERFORMANCE: {
        "title": "Product Performance",
        "calculation": (
            "Performance is calculated from total units sold, total "
            "revenue, and average daily units over the available "
            "90-day sales period."
        ),
        "recommendation_basis": (
            "Use the measured sales performance to support inventory "
            "or merchandising decisions."
        ),
    },

    Intent.SALES_SPIKE: {
        "title": "Sales Spike",
        "calculation": (
            "Recent 7-day daily sales are compared with the previous "
            "30-day daily sales baseline."
        ),
        "recommendation_basis": (
            "Investigate unusually strong recent demand and consider "
            "checking stock availability and replenishment."
        ),
    },

    Intent.SALES_DROP: {
        "title": "Sales Drop",
        "calculation": (
            "Recent 7-day daily sales are compared with the previous "
            "30-day daily sales baseline."
        ),
        "recommendation_basis": (
            "Investigate significant declines before taking corrective "
            "action; the available data does not prove the cause."
        ),
    },

    Intent.GENERAL_INVENTORY: {
        "title": "General Inventory Overview",
        "calculation": (
            "The overview combines deterministic stock-out, overstock, "
            "and non-moving inventory analysis."
        ),
        "recommendation_basis": (
            "Prioritize urgent stock risks first, then review excess "
            "and non-moving inventory."
        ),
    },
}


def build_evidence(
    intent: Intent,
    question: str,
    analytics_result: Any,
) -> Dict[str, Any]:
    """
    Build a standardized evidence package.

    Args:
        intent:
            Detected manager question intent.

        question:
            Original manager question.

        analytics_result:
            Actual result returned by analytics.py.

    Returns:
        Structured evidence dictionary.
    """

    if not isinstance(intent, Intent):
        intent = Intent(intent)

    if intent == Intent.CANNOT_ANSWER:
        return {
            "question": question,
            "intent": intent.value,
            "answerable": False,
            "evidence": [],
            "calculation_rule": None,
            "recommendation_basis": None,
            "assumptions": [
                "The available retail dataset does not reliably "
                "answer this question."
            ],
        }

    rule = ANALYTIC_RULES.get(intent)

    if rule is None:
        return {
            "question": question,
            "intent": intent.value,
            "answerable": False,
            "evidence": [],
            "calculation_rule": None,
            "recommendation_basis": None,
            "assumptions": [
                "No deterministic analytics rule is defined for "
                "this intent."
            ],
        }

    return {
        "question": question,
        "intent": intent.value,
        "answerable": True,
        "evidence": analytics_result,
        "calculation_rule": rule["calculation"],
        "recommendation_basis": rule["recommendation_basis"],
        "assumptions": [
            "All numerical values come from the local SQLite "
            "retail dataset.",
            "Analytics calculations are deterministic.",
            "The evidence does not prove the underlying cause of "
            "a sales change unless a recorded business event "
            "supports that explanation.",
        ],
    }


def summarize_evidence(evidence_package: Dict[str, Any]) -> Dict[str, Any]:
    """
    Return a compact summary of an evidence package.

    Useful for debugging and later API responses.
    """

    evidence = evidence_package.get("evidence", [])

    if isinstance(evidence, list):
        record_count = len(evidence)

    elif isinstance(evidence, dict):
        record_count = sum(
            len(value)
            for value in evidence.values()
            if isinstance(value, list)
        )

    else:
        record_count = 0

    return {
        "intent": evidence_package.get("intent"),
        "answerable": evidence_package.get("answerable", False),
        "record_count": record_count,
        "has_calculation_rule": bool(
            evidence_package.get("calculation_rule")
        ),
        "has_recommendation_basis": bool(
            evidence_package.get("recommendation_basis")
        ),
    }


if __name__ == "__main__":

    print("=" * 70)
    print("RETAIL COPILOT - EVIDENCE LAYER TEST")
    print("=" * 70)

    sample_evidence = [
        {
            "store_name": "Delhi Market Store",
            "product_name": "Wheat Flour 5kg",
            "closing_stock": 0,
            "reorder_level": 34,
            "days_of_stock": 0.0,
            "risk_level": "CRITICAL",
        }
    ]

    package = build_evidence(
        Intent.STOCKOUT_RISK,
        "What products are running out?",
        sample_evidence,
    )

    print()
    print("Intent       :", package["intent"])
    print("Answerable   :", package["answerable"])
    print("Evidence     :", len(package["evidence"]))
    print("Calculation  :", package["calculation_rule"])
    print("Recommendation:")
    print(package["recommendation_basis"])

    print()
    print("Summary:")
    print(summarize_evidence(package))

    print()
    print("=" * 70)
    print("EVIDENCE LAYER TEST COMPLETE")
    print("=" * 70)