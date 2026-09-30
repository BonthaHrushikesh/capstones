from __future__ import annotations

import datetime as dt
import uuid

from . import analytics, anomaly, forecasting
from .guardrails import check_context_scope, check_data_scope, check_request_scope
from .keyword_search import search as keyword_search
from .llm import explain_with_llm
from .nlp import understand

SUBMETER_LABELS = {
    1: "Sub-meter 1 (kitchen group)",
    2: "Sub-meter 2 (laundry-room group)",
    3: "Sub-meter 3 (water heating and air-conditioning group)",
}
SUBMETER_DEFINITIONS = {
    1: "The dataset groups dishwasher, oven, and microwave electricity here; it excludes refrigerator and lighting.",
    2: "The dataset groups washing machine, tumble dryer, refrigerator, and lighting electricity here.",
    3: "The dataset groups electric water heating and air-conditioning electricity here.",
}


def _follow_up_suggestions(intents: set[str], focus: dict | None = None) -> list[str]:
    focus = focus or {}
    if focus.get("forecast_accuracy"):
        return ["Show a forecast for the next 24 hours", "Explain the forecast model"]
    if "anomaly" in intents:
        return ["What is the anomaly score based on?", "Compare the strongest flag with the prior week"]
    if "forecast" in intents:
        return ["How accurate is this forecast?", "What does the forecast model use?"]
    if "usage_mix" in intents:
        return ["What does each sub-meter include?", "Which clock-hours have the highest demand?"]
    if "change" in intents:
        return ["Which weekday has the highest average demand?", "Show the demand profile by hour"]
    return ["Which clock-hours have the highest demand?", "Show unusual readings", "What is the estimated usage breakdown?"]


def _daily_rows_for_weekday(summary: dict, weekday: str) -> list[dict]:
    target = dt.datetime.strptime(weekday, "%A").weekday()
    return [row for row in summary.get("daily", [])
            if dt.date.fromisoformat(row["date"]).weekday() == target]


def _weekday_comparison(summary: dict) -> str | None:
    weekday_rows = []
    weekend_rows = []
    for row in summary.get("daily", []):
        day = dt.date.fromisoformat(row["date"]).weekday()
        (weekend_rows if day >= 5 else weekday_rows).append(row["mean_kw"])
    if not weekday_rows or not weekend_rows:
        return None
    weekday_mean = sum(weekday_rows) / len(weekday_rows)
    weekend_mean = sum(weekend_rows) / len(weekend_rows)
    delta = weekend_mean - weekday_mean
    relation = "higher" if delta > 0 else "lower" if delta < 0 else "the same as"
    comparison = f"{abs(delta):.3f} kW {relation}" if delta else relation
    return (f"On average, power use was {weekday_mean:.3f} kW on weekdays and {weekend_mean:.3f} kW on weekends. "
            f"Weekend use was {comparison} than weekday use in the chosen dates.")


def _weekday_change_answer(summary: dict, weekday: str) -> str:
    by_date = {dt.date.fromisoformat(row["date"]): row for row in summary.get("daily", [])}
    changes = []
    target_day = dt.datetime.strptime(weekday, "%A").weekday()
    for day, row in by_date.items():
        previous = by_date.get(day - dt.timedelta(days=1))
        if day.weekday() == target_day and previous:
            changes.append((day, previous, row["mean_kw"] - previous["mean_kw"]))
    if not changes:
        rows = [row for day, row in by_date.items() if day.weekday() == target_day]
        if rows:
            mean = sum(row["mean_kw"] for row in rows) / len(rows)
            return (f"Average power use on {weekday} was {mean:.3f} kW. There is not enough earlier data in the chosen dates "
                    "to compare it with the previous day, and meter data cannot show why it changed.")
        return f"There are no {weekday} readings in the selected range."
    day, previous, delta = max(changes, key=lambda item: item[2])
    direction = "increased" if delta >= 0 else "decreased"
    return (f"On {day.isoformat()}, average power use {direction} by {abs(delta):.3f} kW. "
            f"It moved from {previous['mean_kw']:.3f} kW on {day - dt.timedelta(days=1)} to "
            f"{by_date[day]['mean_kw']:.3f} kW. The data shows the change, but not why it happened.")


def _demand_answer(summary: dict, focus: dict) -> str:
    start, end = summary["start"][:10], summary["end"][:10]
    if focus.get("weekday"):
        weekday = focus["weekday"]
        rows = _daily_rows_for_weekday(summary, weekday)
        if not rows:
            return f"There are no {weekday} readings in the selected range ({start} to {end})."
        mean = sum(row["mean_kw"] for row in rows) / len(rows)
        peak_day = max(rows, key=lambda row: row["peak_kw"])
        daily_energy = sum(row["energy_kwh"] for row in rows) / len(rows)
        return (f"Across {len(rows)} {weekday}s from {start} to {end}, average power use was {mean:.3f} kW per hour "
                f"and estimated energy use averaged {daily_energy:.1f} kWh per day. The highest one-hour average on those days "
                f"was {peak_day['peak_kw']:.3f} kW on {peak_day['date']}.")
    if focus.get("weekend_comparison"):
        return _weekday_comparison(summary) or "The selected range needs at least one weekday and one weekend day for this comparison."
    if focus.get("minimum"):
        return (f"The lowest average power use from {start} to {end} was "
                f"{summary['min_kw']:.3f} kW at {summary['min_at'].replace('T', ' ')}.")
    if focus.get("peak_hours"):
        profile = sorted(summary.get("hourly_profile", []), key=lambda row: row["mean_kw"], reverse=True)[:3]
        hours = ", ".join(f"{row['hour']:02d}:00 (average {row['mean_kw']:.3f} kW)" for row in profile)
        return (f"The three busiest times of day from {start} to {end} were {hours}. "
                f"These are average values for each hour. The highest one-hour average was {summary['max_kw']:.3f} kW at {summary['max_at'].replace('T', ' ')}.")
    if focus.get("peak_demand"):
        return (f"The highest one-hour average demand from {start} to {end} was {summary['max_kw']:.3f} kW, "
                f"recorded at {summary['max_at'].replace('T', ' ')}.")
    if focus.get("total_energy"):
        return (f"From {start} to {end}, estimated energy use was {summary['total_energy_kwh']:.1f} kWh. "
                f"This uses {summary['hours']:,} hourly readings, and average power use was {summary['mean_kw']:.3f} kW.")
    if focus.get("average_demand"):
        return (f"Average household demand from {start} to {end} was {summary['mean_kw']:.3f} kW, "
                f"calculated from {summary['hours']:,} hourly readings.")
    if focus.get("trend"):
        days = summary.get("daily", [])
        if len(days) >= 2:
            first, last = days[0], days[-1]
            delta = last["mean_kw"] - first["mean_kw"]
            direction = "increased" if delta > 0 else "decreased" if delta < 0 else "was unchanged"
            return (f"Between {first['date']} and {last['date']}, the daily average {direction} by "
                    f"{abs(delta):.3f} kW, from {first['mean_kw']:.3f} to {last['mean_kw']:.3f} kW. "
                    "This compares the first and last daily averages in the selected period.")
        return "There are not enough daily readings in this selected period to describe a trend."
    return (f"From {start} to {end}, average power use was {summary['mean_kw']:.3f} kW and estimated energy use was "
            f"{summary['total_energy_kwh']:.1f} kWh. The highest one-hour average was {summary['max_kw']:.3f} kW at "
            f"{summary['max_at'].replace('T', ' ')}. {summary['top_weekday']} had the highest average power use of the week.")


def _meter_answer(summary: dict, focus: dict) -> str:
    means = summary["measurement_means"]
    measurement = focus.get("measurement")
    labels = {
        "voltage": ("Mean household voltage", means["voltage_v"], "V"),
        "current": ("Mean household current intensity", means["current_a"], "A"),
        "reactive_power": ("Mean household reactive power", means["reactive_power_kw"], "kW"),
        "active_power": ("Mean household active power", summary["mean_kw"], "kW"),
    }
    if measurement in labels:
        label, value, unit = labels[measurement]
        return f"{label} from {summary['start'][:10]} to {summary['end'][:10]} was {value:.2f} {unit}."
    return (f"From {summary['start'][:10]} to {summary['end'][:10]}, average voltage was {means['voltage_v']:.2f} V, "
            f"average current was {means['current_a']:.2f} A, and reactive power was {means['reactive_power_kw']:.3f} kW.")


def _submeter_answer(summary: dict, focus: dict) -> str:
    mix = summary["energy_mix_kwh"]
    number = focus.get("submeter")
    if number:
        key = f"submeter_{number}"
        label = SUBMETER_LABELS[number]
        amount = mix[key]
        share = amount / summary["total_energy_kwh"] * 100 if summary["total_energy_kwh"] else 0.0
        if focus.get("appliance"):
            definition = SUBMETER_DEFINITIONS[number]
            return (f"The dataset does not measure {focus['appliance']} by itself; it is part of a group. {label} used "
                    f"{amount:.1f} kWh ({share:.1f}% of estimated household energy use) from "
                    f"{summary['start'][:10]} to {summary['end'][:10]}. {definition}")
        return (f"{label} used an estimated {amount:.1f} kWh ({share:.1f}% of estimated household energy use) "
                f"from {summary['start'][:10]} to {summary['end'][:10]}. "
                f"{SUBMETER_DEFINITIONS[number]}")
    ranked = sorted(mix.items(), key=lambda item: item[1], reverse=True)
    parts = ", ".join(f"{name.replace('_', ' ')}: {value:.1f} kWh" for name, value in ranked)
    answer = (f"Estimated household energy use from {summary['start'][:10]} to {summary['end'][:10]} was "
            f"{summary['total_energy_kwh']:.1f} kWh. By group: {parts}. "
            "These groups cannot show the use of one individual appliance, and 'other' is the energy left after the listed groups.")
    if focus.get("appliance_group_question"):
        answer += " The dataset cannot identify which individual appliance used the most."
    return answer


def ask(question: str, start: str | None = None, end: str | None = None, context: str | None = None) -> dict:
    q = (question or "").strip()
    if not q:
        return {"status": "clarification_needed", "answer": "Please enter a question about this energy dataset.", "trace": []}

    cost_guardrail = check_data_scope(q)
    if cost_guardrail:
        return {"status": "clarification_needed", "answer": cost_guardrail["answer"],
                "trace_id": str(uuid.uuid4()), "trace": [{"agent": cost_guardrail["agent"], "finding": cost_guardrail["finding"]}],
                "evidence": {}, "nlp": understand(q),
                "suggested_questions": ["How much energy was used?", "When was household demand highest?"]}

    query_nlp = understand(q)
    focus = query_nlp["focus"]
    intents = set(query_nlp["intents"])
    used_context = False
    if context and check_context_scope(q, context):
        contextual_intents = set(understand(context)["intents"])
        if contextual_intents:
            intents.update(contextual_intents)
            used_context = True
    if focus.get("submeter") and not focus.get("definition"):
        intents.add("usage_mix")
    if focus.get("definition") and (focus.get("submeter") or focus.get("measurement")):
        intents.add("method_lookup")
        intents.discard("usage_mix")
    wants_anomaly = "anomaly" in intents
    wants_forecast_accuracy = bool(focus.get("forecast_accuracy"))
    wants_forecast = "forecast" in intents or wants_forecast_accuracy
    wants_mix = "usage_mix" in intents
    wants_change = "change" in intents
    wants_method = "method_lookup" in intents
    wants_meter = ("meter_lookup" in intents and focus.get("submeter") is None
                   and not focus.get("definition") and not wants_mix)
    wants_overview = ("demand_summary" in intents
                      and not (wants_anomaly or wants_forecast or wants_mix or wants_change or wants_method or wants_meter)
                      and not focus.get("definition"))

    request_guardrail = check_request_scope(intents)
    if request_guardrail:
        return {"status": "clarification_needed", "answer": request_guardrail["answer"],
                "supported_topics": request_guardrail.get("supported_topics"),
                "trace_id": str(uuid.uuid4()), "trace": [{"agent": request_guardrail["agent"], "finding": request_guardrail["finding"]}],
                "evidence": {}, "nlp": query_nlp,
                "suggested_questions": ["Summarize household demand", "Show unusual readings", "Forecast demand"]}

    summary = analytics.summary(start, end)
    if "error" in summary:
        return {"status": "no_data", "answer": summary["error"], "trace_id": str(uuid.uuid4()),
                "trace": [{"agent": "Energy Data Analyst", "finding": "No readings matched the selected range."}],
                "evidence": {"summary": {}}, "nlp": query_nlp, "suggested_questions": []}

    effective_nlp = {**query_nlp, "effective_intents": sorted(intents), "resolved_from_context": used_context}
    nlp_finding = f"Intents: {', '.join(sorted(intents)) or 'unknown'}; confidence {query_nlp['confidence']:.2f}"
    if used_context:
        nlp_finding += "; resolved as a short follow-up using recent conversation context"
    trace = [{"agent": "NLP Query Understanding", "finding": nlp_finding},
             {"agent": "Energy Data Analyst", "finding": "; ".join(summary["evidence"])}]

    anomalies = anomaly.detect(start, end, limit=5) if wants_anomaly else None
    horizon = focus["forecast_horizon_hours"]
    forecast = forecasting.forecast(horizon, start, end) if wants_forecast and not wants_forecast_accuracy else None
    forecast_evaluation = None
    forecast_evaluation_error = None
    if wants_forecast_accuracy:
        try:
            forecast_evaluation = analytics.evaluation(start, end)
        except ValueError as exc:
            forecast_evaluation_error = str(exc)
    if wants_anomaly:
        trace.append({"agent": "Anomaly Investigator",
                      "finding": f"Screened {anomalies['scope_hours']:,} hours and returned {anomalies['count']:,} statistical candidates.",
                      "method": anomalies["method"]})
    if wants_forecast and wants_forecast_accuracy:
        if forecast_evaluation:
            trace.append({"agent": "Forecast Specialist", "finding": f"Evaluated {forecast_evaluation['model']} on a chronological {forecast_evaluation['test_hours']}-hour holdout.", "method": "MAE, RMSE, and MAPE"})
        else:
            trace.append({"agent": "Forecast Specialist", "finding": forecast_evaluation_error or "Forecast evaluation unavailable."})
    elif wants_forecast:
        trace.append({"agent": "Forecast Specialist",
                      "finding": f"Produced a {forecast['horizon_hours']}-hour baseline averaging {forecast['mean_kw']:.3f} kW.",
                      "method": forecast["model"]})

    retrieved = keyword_search(q, summary, anomalies, forecast)
    trace.append({"agent": "Energy Knowledge Search",
                  "finding": f"Retrieved {retrieved['result_count']} evidence passages using {retrieved['method']}"})

    statements = []
    if wants_overview:
        statements.append(_demand_answer(summary, focus))
    if wants_anomaly:
        flags = anomalies["flags"]
        if flags:
            strongest = flags[0]
            statements.append(
                f"I found {anomalies['count']:,} unusual readings worth checking. The largest was at "
                f"{strongest['timestamp']}: power use was {strongest['observed_kw']:.3f} kW, compared with the usual "
                f"{strongest['baseline_kw']:.3f} kW for that day and hour. This is a signal to review, not proof of a fault.")
        else:
            statements.append("I did not find readings unusual enough to flag in the chosen dates. This does not prove that equipment had no faults.")
    if wants_forecast:
        if wants_forecast_accuracy:
            if forecast_evaluation:
                statements.append(
                    f"On a chronological holdout of {forecast_evaluation['test_hours']:,} hours, the "
                    f"{forecast_evaluation['model']} scored MAE {forecast_evaluation['mae_kw']:.4f} kW, "
                    f"RMSE {forecast_evaluation['rmse_kw']:.4f} kW, and MAPE {forecast_evaluation['mape_percent']:.2f}%. "
                    f"{forecast_evaluation['note']}")
            else:
                statements.append(forecast_evaluation_error or "Forecast evaluation is unavailable for this date range.")
        else:
            statements.append(
                f"For the next {forecast['horizon_hours']} hours, expected average power use is {forecast['mean_kw']:.3f} kW. "
                f"This estimate uses readings through {forecast['history_end']}.")
            if focus.get("forecast_horizon_was_capped"):
                statements.append("I limited the forecast to the supported maximum of 168 hours (7 days).")
            if forecast["stale_data_warning"]:
                statements.append("The source data is historical, so use this as a planning estimate rather than a live demand prediction.")
    if wants_mix:
        statements.append(_submeter_answer(summary, focus))
    if wants_meter:
        statements.append(_meter_answer(summary, focus))
    if wants_change:
        if wants_anomaly and not focus.get("weekday"):
            statements.append("The meter data can identify when power differed from its usual pattern, but it cannot establish the cause; it contains no appliance event logs, occupancy, or weather records.")
        elif focus.get("weekday"):
            statements.append(_weekday_change_answer(summary, focus["weekday"]))
        else:
            shift = summary["largest_daily_rise"]
            if shift:
                leaders = sorted(shift["submeter_kwh_change"].items(), key=lambda item: abs(item[1]), reverse=True)
                source, delta = leaders[0]
                direction = "increased" if shift["mean_kw_change"] >= 0 else "decreased"
                statements.append(
                    f"The biggest day-to-day change was a {direction} of {abs(shift['mean_kw_change']):.3f} kW in average power use "
                    f"on {shift['date']} compared with {shift['previous_date']}. {source.replace('_', ' ')} changed by "
                    f"{delta:+.2f} kWh, the largest group change. The data cannot show the cause because it has no weather, occupancy, or appliance-event records.")
            else:
                statements.append("This selected range needs at least two days of readings to compare day-to-day demand changes.")
    if wants_method:
        method_results = [item for item in retrieved["results"] if item["kind"] == "method"][:2]
        if method_results:
            statements.extend(f"{item['title']}: {item['text']}" for item in method_results)
        else:
            statements.append("I could not find a matching method note. Ask about the dataset, meter units, anomaly screen, forecast method, or sub-meter definitions.")

    if not statements:
        statements.append("I could not tell which supported energy metric you mean. Ask about average or peak demand, total energy, unusual readings, forecast, voltage, current, or sub-meter groups.")
    if wants_anomaly:
        recommendation = "Use anomaly candidates to prioritize a review against meter or equipment records; do not treat a flag alone as a confirmed fault."
    elif wants_forecast:
        recommendation = "Treat this as a historical planning baseline and refresh it when newer meter readings are available."
    elif wants_mix:
        recommendation = "Sub-meter totals are grouped estimates; individual appliance use is not separately measured."
    else:
        recommendation = "Use the selected date scope when comparing results across the dashboard."
    trace.extend([
        {"agent": "Energy Insight Synthesizer", "finding": "Combined only requested analyses; reported facts are tied to the selected household-data scope."},
        {"agent": "Decision Guide", "finding": recommendation},
    ])

    evidence_keys = ("start", "end", "hours", "mean_kw", "max_kw", "max_at", "min_kw", "min_at",
                     "p95_kw", "top_weekday", "peak_hours", "hourly_profile", "weekday_profile",
                     "total_energy_kwh", "energy_mix_kwh", "measurement_means", "largest_daily_rise", "evidence")
    summary_evidence = {key: summary[key] for key in evidence_keys if key in summary}
    deterministic_answer = " ".join(statements)
    answer, llm_status = explain_with_llm(q, deterministic_answer,
                                          {"summary": summary_evidence, "anomalies": anomalies, "forecast": forecast,
                                           "forecast_evaluation": forecast_evaluation})
    trace.append({"agent": "Grounded language response", "finding": llm_status["message"],
                  "method": llm_status["provider"]})
    return {"status": "answered", "trace_id": str(uuid.uuid4()), "question": q, "answer": answer,
            "trace": trace, "evidence": {"summary": summary_evidence, "anomalies": anomalies, "forecast": forecast},
            "nlp": effective_nlp, "search_results": retrieved["results"], "llm": llm_status,
            "suggested_questions": _follow_up_suggestions(intents, focus),
            "workflow": "Query understanding -> scoped household evidence -> requested specialist analyses -> grounded answer."}
