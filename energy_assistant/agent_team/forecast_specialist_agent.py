from __future__ import annotations

from .. import forecasting


def run(horizon: int = 24, start: str | None = None, end: str | None = None) -> dict:
    forecast = forecasting.forecast(horizon, start, end)
    return {
        "agent": "Forecast Specialist",
        "title": "Historical outlook",
        "model": forecast["model"],
        "mean_kw": forecast["mean_kw"],
        "forecast": forecast["forecast"],
        "caveat": forecast["caveat"],
        "fallback_used": forecast["fallback_used"],
        "text": f"The {forecast['model']} estimates a {forecast['mean_kw']:.3f} kW average over the next {horizon} hours.",
    }
