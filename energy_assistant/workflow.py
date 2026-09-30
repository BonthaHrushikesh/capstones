from __future__ import annotations

from collections import Counter

from .guardrails import check_request_scope
from .nlp import understand


ROUTE_MAP = {
    "demand_summary": "analytics",
    "anomaly": "anomaly",
    "forecast": "forecast",
    "usage_mix": "analytics",
    "meter_lookup": "analytics",
    "change": "analytics",
    "method_lookup": "insight",
}


def route_question(question: str, context: str | None = None) -> dict:
    """Translate a user question into the specialist route(s) it should use."""
    text = (question or "").strip()
    if not text:
        return {
            "question": text,
            "intents": [],
            "route": [],
            "status": "clarification_needed",
            "reason": "Question text is empty.",
        }

    parsed = understand(text)
    intents = sorted(set(parsed.get("intents", [])))
    if context and not intents:
        follow_up = understand(context)
        intents = sorted(set(follow_up.get("intents", [])))

    routes = []
    for intent in intents:
        route = ROUTE_MAP.get(intent)
        if route and route not in routes:
            routes.append(route)

    guardrail = check_request_scope(set(intents))
    if guardrail:
        return {
            "question": text,
            "intents": intents,
            "route": [],
            "status": "clarification_needed",
            "reason": guardrail["finding"],
            "supported_topics": guardrail.get("supported_topics", []),
            "nlp": parsed,
        }

    if not routes:
        return {
            "question": text,
            "intents": intents,
            "route": [],
            "status": "clarification_needed",
            "reason": "The question did not fit a supported energy-analysis route.",
            "nlp": parsed,
        }

    return {
        "question": text,
        "intents": intents,
        "route": routes,
        "status": "ok",
        "reason": "Routed to specialist evidence collection and synthesis.",
        "nlp": parsed,
    }


def evaluate_query_routing(samples: list[dict] | None = None) -> dict:
    """Run a small built-in routing benchmark and return a pass/fail summary."""
    if samples is None:
        samples = [
            {"question": "What were the peak demand hours this week?", "expected": ["analytics"]},
            {"question": "Which periods show unusual readings?", "expected": ["anomaly"]},
            {"question": "Forecast demand for the next 24 hours.", "expected": ["forecast"]},
            {"question": "How much energy came from the kitchen sub-meter?", "expected": ["analytics"]},
            {"question": "Which periods show an unusual demand rise on Tuesday?", "expected": ["analytics", "anomaly"]},
        ]

    results = []
    route_counter: Counter[str] = Counter()
    for sample in samples:
        question = sample["question"]
        result = route_question(question, sample.get("context"))
        expected = set(sample.get("expected", []))
        actual = set(result.get("route", []))
        ok = bool(expected and expected.issubset(actual)) or (not expected and result["status"] == "clarification_needed")
        route_counter.update(actual)
        results.append({
            "question": question,
            "expected": sorted(expected),
            "actual": sorted(actual),
            "status": "ok" if ok else "failed",
        })

    passed = sum(1 for item in results if item["status"] == "ok")
    return {
        "total": len(results),
        "passed": passed,
        "failed": len(results) - passed,
        "routes": dict(sorted(route_counter.items())),
        "results": results,
    }


__all__ = ["route_question", "evaluate_query_routing", "ROUTE_MAP"]
