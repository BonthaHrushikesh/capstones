from __future__ import annotations

import pandas as pd

from .data import POWER, select_hours
from .fallbacks import choose_forecast_strategy


def forecast(horizon: int = 24, start: str | None = None, end: str | None = None) -> dict:
    # GUARDRAIL SHOWCASE 3: bound the requested horizon even for non-API callers.
    horizon = min(max(int(horizon), 1), 168)
    history = select_hours(start, end)
    # Exclude partial hours so the forecast is anchored to a reasonably complete observation.
    series = history.loc[history["minute_count"] >= 45, POWER].dropna()
    if len(series) < 3:
        raise ValueError("There are too few complete hourly readings to produce a safe forecast.")
    recent = series.iloc[-168:]
    continuous = len(recent) >= 168 and (recent.index.to_series().diff().dropna() == pd.Timedelta(hours=1)).all()
    fallback_used = False
    if continuous:
        model = "Weekly seasonal-naive"
        values = [float(recent.iloc[i % 168]) for i in range(horizon)]
    else:
        recent_day = series.iloc[-24:]
        day_continuous = len(recent_day) >= 24 and (recent_day.index.to_series().diff().dropna() == pd.Timedelta(hours=1)).all()
        strategy = choose_forecast_strategy(len(series), continuous, day_continuous)
        fallback_used = strategy["fallback_used"]
        if strategy["model"] == "Weekly seasonal-naive":
            model = strategy["model"]
            values = [float(recent.iloc[i % 168]) for i in range(horizon)]
        elif strategy["model"] == "Daily seasonal fallback (24-hour cycle)":
            model = strategy["model"]
            values = [float(recent_day.iloc[i % 24]) for i in range(horizon)]
        elif strategy["model"] == "Recent-median fallback":
            model = strategy["model"]
            baseline = float(series.iloc[-24:].median())
            values = [baseline] * horizon
        else:
            model = strategy["model"]
            baseline = float(series.median()) if len(series) else 0.0
            values = [baseline] * horizon
    history_end = series.index[-1]
    stamps = pd.date_range(history_end + pd.Timedelta(hours=1), periods=horizon, freq="h")
    now = pd.Timestamp.now()
    stale_data = history_end < now - pd.Timedelta(days=7)
    caveat = "Forecast uses a weekly history pattern; weather and occupancy are unavailable."
    if fallback_used:
        caveat += " A lower-history fallback was selected because the latest observations do not contain a complete continuous week."
    if stale_data:
        caveat += f" Historical-data guardrail: source readings end at {history_end}; this is not a live forecast for today."
    return {"model": model, "fallback_used": fallback_used, "stale_data_warning": stale_data,
            "history_end": history_end.isoformat(),
            "horizon_hours": horizon, "mean_kw": round(sum(values)/horizon, 3),
            "forecast": [{"timestamp": ts.isoformat(), "kw": round(v, 3)} for ts,v in zip(stamps, values)],
            "caveat": caveat}
