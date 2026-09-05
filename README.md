TRACK_ID=PS03

# Retail Sales & Inventory Copilot

TRACK_ID=PS03

## What this project does

Retail Sales & Inventory Copilot is a manager-focused assistant for small retail operations.

It answers natural-language questions about sales and inventory using a locally generated retail dataset.

The application can identify:

- Stock-out risks
- Overstocked inventory
- Non-moving stock
- Sales spikes
- Sales drops
- Product performance
- General inventory attention areas

The system provides the actual numbers and evidence behind its answers.

## How it works

The application separates deterministic business logic from GenAI explanation.

```text
Manager Question
       ↓
Intent Detection
       ↓
Deterministic Analytics
       ↓
SQLite Retail Data
       ↓
Evidence + Calculations
       ↓
Gemini Explanation
       ↓
Manager-Friendly Answer