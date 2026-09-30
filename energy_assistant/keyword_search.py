"""Keyword retrieval over WattWise methods and computed energy evidence."""
from __future__ import annotations

import math

from .nlp import normalize_tokens, understand

KNOWLEDGE = [
    ("Dataset scope", "This dataset contains one household from December 2006 through November 2010. It has no region ids, grid operations, weather, occupancy, or verified equipment fault labels."),
    ("Anomaly method", "Unusual consumption is screened using a robust score against the same weekday and hour median absolute deviation. A score threshold of 4.5 identifies review candidates, not confirmed faults."),
    ("Forecast method", "The weekly seasonal forecast repeats the matching hour from the prior week. It is a historical baseline and not a live grid forecast; no weather or occupancy inputs are present."),
    ("Data preparation", "The source is semicolon delimited. Question-mark readings are missing, timestamps are parsed day first, short internal gaps are interpolated, and remaining missing meter readings use column median."),
    ("Sub-meter 1 meaning", "Sub-meter 1 represents kitchen electricity such as dishwasher, oven, and microwave; refrigerator and lighting are excluded in the dataset definition."),
    ("Sub-meter 2 meaning", "Sub-meter 2 represents laundry-room electricity, including washing machine, tumble dryer, refrigerator, and lighting, per the dataset definition."),
    ("Sub-meter 3 meaning", "Sub-meter 3 represents electric water heating and air-conditioning energy in the dataset."),
    ("Energy units", "Global active power is measured in kilowatts. Sub-meter values represent watt-hours per minute; household usage mix is an estimate and Other is a residual."),
    ("Voltage measurement", "Voltage is the household supply voltage measured in volts. This single-home dataset does not describe regional voltage conditions."),
    ("Reactive power measurement", "Global reactive power is a household electrical measurement in kilowatts; it is separate from global active power."),
    ("Current measurement", "Global intensity is household electrical current measured in amperes."),
]


def _documents(summary: dict, anomalies: dict | None, forecast: dict | None) -> list[dict]:
    docs = [{"title": title, "text": text, "kind": "method"} for title, text in KNOWLEDGE]
    peak_hours = sorted(summary.get("hourly_profile", []), key=lambda row: row["mean_kw"], reverse=True)[:3]
    peak_text = ", ".join(f"{row['hour']:02d}:00 ({row['mean_kw']} kW mean)" for row in peak_hours)
    docs.extend([
        {"title": "Overall demand", "text": f"Average active power {summary['mean_kw']} kW; peak hourly mean {summary['max_kw']} kW at {summary['max_at']}; lowest hourly mean {summary.get('min_kw')} kW at {summary.get('min_at')}; total estimated active energy {summary['total_energy_kwh']} kWh; p95 {summary['p95_kw']} kW; highest average weekday {summary['top_weekday']}; records from {summary['start']} to {summary['end']}.", "kind": "metric"},
        {"title": "Peak demand clock-hours", "text": f"The clock-hours with the highest average active power in this selected range were {peak_text}. These are average values by hour of day, not a list of distinct events.", "kind": "trend"},
        {"title": "Average demand by weekday", "text": "; ".join(f"{row['weekday']}: {row['mean_kw']} kW" for row in summary.get('weekday_profile', [])), "kind": "trend"},
        {"title": "Largest day-to-day demand change", "text": str(summary.get("largest_daily_rise")), "kind": "change"},
    ])
    for name, value in summary.get("measurement_means", {}).items():
        docs.append({"title": f"Average {name.replace('_',' ')}", "text": f"Mean {name.replace('_',' ')} across this period is {value}.", "kind": "measurement"})
    for name, amount in summary.get("energy_mix_kwh", {}).items():
        docs.append({"title": f"{name.replace('_',' ')} energy", "text": f"{name.replace('_',' ')} estimated energy use is {amount} kWh in the selected data range.", "kind": "submeter"})
    for row in summary.get("monthly", []):
        docs.append({"title": f"Monthly demand {row['month']}", "text": f"Mean hourly demand in {row['month']} was {row['mean_kw']} kW.", "kind": "trend"})
    for row in summary.get("daily", []):
        docs.append({"title": f"Daily demand {row['date']}", "text": f"On {row['date']}, mean active power was {row['mean_kw']} kW and peak hour was {row['peak_kw']} kW.", "kind": "trend"})
    if anomalies:
        for item in anomalies.get("flags", []):
            docs.append({"title": f"Unusual hour {item['timestamp']}", "text": f"Observed {item['observed_kw']} kW, baseline {item['baseline_kw']} kW, robust anomaly score {item['score']}.", "kind": "anomaly"})
    if forecast:
        for item in forecast.get("forecast", []):
            docs.append({"title": f"Forecast {item['timestamp']}", "text": f"Expected hourly active power {item['kw']} kW on {item['timestamp']} using {forecast['model']}.", "kind": "forecast"})
    return docs


def search(query: str, summary: dict, anomalies: dict | None = None, forecast: dict | None = None, limit: int = 8) -> dict:
    """Rank evidence with normalized keyword overlap and an exact-phrase boost."""
    # KEYWORD SEARCH SHOWCASE: transparent term scoring keeps every result inspectable.
    terms = normalize_tokens(query)
    if not terms:
        return {"query": query, "results": [], "message": "Enter a few energy-related keywords to search the evidence."}
    documents = _documents(summary, anomalies, forecast)
    unique_terms = set(terms)
    parsed = understand(query)
    intent_kinds = {
        "anomaly": {"anomaly"}, "forecast": {"forecast"}, "usage_mix": {"submeter"},
        "meter_lookup": {"measurement"}, "method_lookup": {"method"},
        "demand_summary": {"metric", "trend"}, "change": {"change", "trend"},
    }
    preferred_kinds = set().union(*(intent_kinds.get(intent, set()) for intent in parsed["intents"]))
    scored = []
    for doc in documents:
        doc_terms = set(normalize_tokens(doc["title"] + " " + doc["text"]))
        matched = unique_terms & doc_terms
        if not matched:
            continue
        coverage = len(matched) / len(unique_terms)
        density = len(matched) / max(1, math.sqrt(len(doc_terms)))
        phrase_boost = 0.35 if query.casefold() in (doc["title"] + " " + doc["text"]).casefold() else 0.0
        topic_boost = 0.18 if doc["kind"] in preferred_kinds else 0.0
        score = round(coverage * 0.7 + density * 0.2 + phrase_boost + topic_boost, 3)
        scored.append({"title": doc["title"], "text": doc["text"], "kind": doc["kind"],
                       "score": score, "matched_terms": sorted(matched)})
    scored.sort(key=lambda item: (-item["score"], item["title"]))
    results = scored[:max(1, min(int(limit), 20))]
    return {"query": query, "normalized_terms": terms, "result_count": len(results), "results": results,
            "method": "canonicalized keyword overlap, phrase match, and intent-aware evidence ranking"}
