from __future__ import annotations

from .. import anomaly


def run(start: str | None = None, end: str | None = None, limit: int = 5) -> dict:
    results = anomaly.detect(start, end, limit)
    strongest = results["flags"][0] if results["flags"] else None
    return {
        "agent": "Anomaly Investigator",
        "title": "Unusual-hour screen",
        "count": results["count"],
        "method": results["method"],
        "text": (
            f"{results['count']:,} candidate hours met the robust screening threshold."
            if strongest else "No readings crossed the anomaly screening threshold."
        ),
        "strongest": strongest,
        "evidence": results,
    }
