from __future__ import annotations

from .. import analytics, anomaly


def run(start: str | None = None, end: str | None = None) -> dict:
    summary = analytics.summary(start, end)
    anomalies = anomaly.detect(start, end, limit=5)
    if anomalies["flags"]:
        strongest = anomalies["flags"][0]
        recommendation = {
            "priority": "Review statistical candidate",
            "action": f"Check the meter or appliance records around {strongest['timestamp']}.",
            "reason": (
                f"Observed demand was {strongest['observed_kw']:.3f} kW versus a "
                f"{strongest['baseline_kw']:.3f} kW weekday/hour baseline (score {strongest['score']})."
            ),
            "basis": "Weekday-hour robust MAD screen; candidate is ranked by absolute robust score.",
        }
    else:
        recommendation = {
            "priority": "Establish a baseline",
            "action": "Track the highest-demand periods and compare them with household routines before changing equipment or schedules.",
            "reason": "No hourly readings crossed the anomaly screening threshold in this selected period.",
            "basis": f"Peak demand was {summary['max_kw']:.3f} kW at {summary['max_at']}; mean demand was {summary['mean_kw']:.3f} kW.",
        }
    return {
        "agent": "Decision Guide",
        "title": "Recommended action",
        "period": {"start": summary["start"], "end": summary["end"], "hours": summary["hours"]},
        "recommendation": recommendation,
        "supporting_evidence": [*summary["evidence"], recommendation["reason"]],
        "caveat": "Use this as a review aid for one household. The data has no labeled faults, appliance event logs, occupancy, or weather; it cannot prove a cause or prescribe a grid operation.",
    }
