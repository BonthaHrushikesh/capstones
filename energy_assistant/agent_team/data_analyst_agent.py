from __future__ import annotations

from .. import analytics


def run(start: str | None = None, end: str | None = None) -> dict:
    summary = analytics.summary(start, end)
    return {
        "agent": "Energy Data Analyst",
        "title": "Demand pattern",
        "summary": {
            "start": summary["start"],
            "end": summary["end"],
            "mean_kw": summary["mean_kw"],
            "max_kw": summary["max_kw"],
            "max_at": summary["max_at"],
            "top_weekday": summary["top_weekday"],
        },
        "evidence": summary["evidence"],
        "text": (
            f"For {summary['start'][:10]} to {summary['end'][:10]}, mean demand was {summary['mean_kw']:.3f} kW. "
            f"The highest hourly mean was {summary['max_kw']:.3f} kW at {summary['max_at']}; "
            f"{summary['top_weekday']} had the strongest average weekday demand."
        ),
    }
