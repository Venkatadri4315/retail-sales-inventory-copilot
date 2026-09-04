from enum import Enum


class Intent(str, Enum):
    """Supported manager question types."""

    STOCKOUT_RISK = "stockout_risk"
    OVERSTOCK = "overstock"
    NON_MOVING = "non_moving"
    PRODUCT_PERFORMANCE = "product_performance"
    SALES_SPIKE = "sales_spike"
    SALES_DROP = "sales_drop"
    GENERAL_INVENTORY = "general_inventory"
    CANNOT_ANSWER = "cannot_answer"


INTENT_DESCRIPTIONS = {
    Intent.STOCKOUT_RISK:
        "Identify products that are at risk of running out of stock.",

    Intent.OVERSTOCK:
        "Identify products with excessive inventory compared with demand.",

    Intent.NON_MOVING:
        "Identify products that have inventory but little or no recent sales.",

    Intent.PRODUCT_PERFORMANCE:
        "Show sales performance of a specific product or product-store combination.",

    Intent.SALES_SPIKE:
        "Identify products whose recent sales are significantly above their normal baseline.",

    Intent.SALES_DROP:
        "Identify products whose recent sales are significantly below their normal baseline.",

    Intent.GENERAL_INVENTORY:
        "Answer broad inventory questions using the available inventory analytics.",

    Intent.CANNOT_ANSWER:
        "Use when the available data cannot reliably answer the manager's question.",
}


INTENT_EXAMPLES = {
    Intent.STOCKOUT_RISK: [
        "What products are running out?",
        "Which items are at risk of stock-out?",
        "What do I need to reorder?",
        "Which products have low stock?",
    ],

    Intent.OVERSTOCK: [
        "Which products are overstocked?",
        "What inventory is too high?",
        "Which items have excess stock?",
        "Where do we have too much inventory?",
    ],

    Intent.NON_MOVING: [
        "Which products are not moving?",
        "What products have no recent sales?",
        "Which inventory is sitting unsold?",
        "Show me dead stock.",
    ],

    Intent.PRODUCT_PERFORMANCE: [
        "How did Wheat Flour 5kg perform?",
        "How many units of Cooking Oil 1L did we sell?",
        "What are the sales of Puzzle Book?",
        "How is this product performing?",
    ],

    Intent.SALES_SPIKE: [
        "Which products have sales spikes?",
        "What products are selling much faster than usual?",
        "Which items have unusually high sales?",
        "Show me recent sales increases.",
    ],

    Intent.SALES_DROP: [
        "Which products have sales drops?",
        "What products are selling less than usual?",
        "Which items have declining sales?",
        "Show me products with falling sales.",
    ],

    Intent.GENERAL_INVENTORY: [
        "Give me an inventory overview.",
        "How is our inventory doing?",
        "What is the current inventory situation?",
        "Give me a stock summary.",
    ],

    Intent.CANNOT_ANSWER: [
        "What will our sales be next year?",
        "Why do customers dislike this product?",
        "Which employee caused the sales drop?",
        "What are our competitors doing?",
    ],
}


def get_supported_intents():
    """Return all supported intents with descriptions."""

    return [
        {
            "intent": intent.value,
            "description": description,
        }
        for intent, description in INTENT_DESCRIPTIONS.items()
    ]


def get_intent_description(intent):
    """Return the description for a supported intent."""

    try:
        intent_value = (
            intent if isinstance(intent, Intent)
            else Intent(intent)
        )
    except (ValueError, TypeError) as exc:
        raise ValueError(
            f"Unsupported intent: {intent}"
        ) from exc

    return INTENT_DESCRIPTIONS[intent_value]


def get_intent_examples(intent):
    """Return example questions for a supported intent."""

    try:
        intent_value = (
            intent if isinstance(intent, Intent)
            else Intent(intent)
        )
    except (ValueError, TypeError) as exc:
        raise ValueError(
            f"Unsupported intent: {intent}"
        ) from exc

    return INTENT_EXAMPLES[intent_value]


def is_supported_intent(intent):
    """Return True if the intent is supported."""

    try:
        Intent(intent)
        return True
    except (ValueError, TypeError):
        return False


def get_intent_count():
    """Return the number of supported intents."""

    return len(Intent)


if __name__ == "__main__":

    print("=" * 70)
    print("RETAIL SALES & INVENTORY COPILOT")
    print("SUPPORTED INTENTS")
    print("=" * 70)

    for intent in Intent:

        print()
        print(f"Intent      : {intent.value}")
        print(f"Description : {INTENT_DESCRIPTIONS[intent]}")
        print("Examples:")

        for example in INTENT_EXAMPLES[intent]:
            print(f"  - {example}")

    print()
    print("=" * 70)
    print(f"Total supported intents: {get_intent_count()}")
    print("=" * 70)

    print()
    print("VALIDATION")
    print("-" * 70)

    print(
        "stockout_risk supported:",
        is_supported_intent("stockout_risk")
    )

    print(
        "invalid_intent supported:",
        is_supported_intent("invalid_intent")
    )

    print(
        "Overstock description:",
        get_intent_description(Intent.OVERSTOCK)
    )

    print("=" * 70)
