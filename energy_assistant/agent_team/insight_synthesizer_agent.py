from __future__ import annotations

from .. import analytics, anomaly, forecasting


def run(start: str | None = None, end: str | None = None) -> dict:
    summary = analytics.summary(start, end)
    anomalies = anomaly.detect(start, end, limit=5)
    forecast = forecasting.forecast(24, start, end)
    if anomalies["flags"]:
        strongest = anomalies["flags"][0]
        anomaly_text = (
            f"{anomalies['count']:,} statistical candidates were flagged. The strongest shown was "
            f"{strongest['timestamp']} (score {strongest['score']})."
        )
    else:
        anomaly_text = "No hours crossed the statistical screening threshold in this period."
    rise = summary.get("largest_daily_rise")
    change_text = (
        f"Daily mean demand rose by {rise['mean_kw_change']:+.3f} kW on {rise['date']} compared with {rise['previous_date']}."
        if rise else "This period does not contain two full days to compare day-over-day demand."
    )
    return {
        "agent": "Energy Insight Synthesizer",
        "title": "Integrated brief",
        "period": {"start": summary["start"], "end": summary["end"], "hours": summary["hours"]},
        "findings": [
            {"agent": "Energy Data Analyst", "title": "Demand summary", "text": f"Mean demand was {summary['mean_kw']:.3f} kW; the peak was {summary['max_kw']:.3f} kW at {summary['max_at']}.", "evidence": summary["evidence"]},
            {"agent": "Anomaly Investigator", "title": "Anomaly review", "text": anomaly_text, "evidence": anomalies["flags"][0] if anomalies["flags"] else None, "method": anomalies["method"]},
            {"agent": "Forecast Specialist", "title": "Forecast baseline", "text": f"The next 24-hour baseline averages {forecast['mean_kw']:.3f} kW using {forecast['model']}.", "evidence": {"history_end": forecast["history_end"], "caveat": forecast["caveat"]}},
            {"agent": "Energy Data Analyst", "title": "Demand change", "text": change_text, "evidence": rise},
        ],
        "caveat": "This is one household's historical meter data. Statistical flags are not confirmed faults, and the forecast is not live.",
    }
