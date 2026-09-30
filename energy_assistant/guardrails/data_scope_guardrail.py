from __future__ import annotations

import re


def check_data_scope(question: str) -> dict | None:
    """Prevent unsupported cost-based answers when billing metadata is absent."""
    if re.search(r"\b(cost|costs|bill|bills|price|prices|tariff|dollars?|payment|spent|spending)\b", question, re.IGNORECASE):
        return {
            "status": "clarification_needed",
            "answer": "I can estimate household energy use in kWh, but this dataset has no electricity rates or bill amounts, so I cannot calculate or explain dollar costs. Ask me about energy use, peaks, or changes instead.",
            "agent": "Dataset Scope Guardrail",
            "finding": "No tariff or billing data is available; a cost answer would be unsupported.",
        }
    return None


def evaluate(question: str) -> dict | None:
    return check_data_scope(question)
