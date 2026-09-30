from __future__ import annotations


def check_request_scope(intents: set[str]) -> dict | None:
    """Reject unsupported intents before generating a fabricated analysis."""
    if not intents:
        return {
            "status": "clarification_needed",
            "answer": "I can help with demand summaries, peak hours, unusual readings, demand changes, sub-meter usage, and forecasts. Please rephrase your question around one of those topics.",
            "supported_topics": [
                "demand and peaks",
                "anomalies",
                "forecast",
                "sub-meter breakdown",
                "voltage/current/reactive-power measurements",
                "demand changes",
            ],
            "agent": "Request Guardrail",
            "finding": "Question did not match a supported energy-analysis intent; no analytical claim was generated.",
        }
    return None


def guard(intents: set[str]) -> dict | None:
    return check_request_scope(intents)
