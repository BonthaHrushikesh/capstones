from __future__ import annotations

import re


def check_context_scope(question: str, context: str | None = None) -> bool:
    """Only allow short, referential follow-ups using a recent context window."""
    if not context:
        return False
    follow_up = len(question.split()) <= 8 and bool(
        re.search(
            r"^(and\b|what about\b|how about\b|which (day|date|one)\b|why\b|how so\b|tell me more\b|more\b|explain (that|it|this)\b|what does that\b|what happened then\b|same period\b|on that day\b|was it\b|did it\b)",
            question.lower(),
        )
    )
    return bool(follow_up)


def evaluate(question: str, context: str | None = None) -> bool:
    return check_context_scope(question, context)
