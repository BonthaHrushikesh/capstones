from __future__ import annotations


def choose_forecast_strategy(history_points: int, has_continuous_week: bool, has_continuous_day: bool) -> dict:
    """Choose the safest forecast strategy when source data is partial."""
    if has_continuous_week:
        return {
            "model": "Weekly seasonal-naive",
            "fallback_used": False,
            "reason": "A full continuous week is available in the selected history window.",
        }
    if has_continuous_day:
        return {
            "model": "Daily seasonal fallback (24-hour cycle)",
            "fallback_used": True,
            "reason": "A full day is available, so a short-cycle fallback is used instead of a longer seasonal baseline.",
        }
    if history_points >= 24:
        return {
            "model": "Recent-median fallback",
            "fallback_used": True,
            "reason": "Not enough continuity was present for a seasonal cycle, so the recent median provides a bounded baseline.",
        }
    return {
        "model": "Insufficient-history fallback",
        "fallback_used": True,
        "reason": "There is too little complete history to form a defensible forecast. The result should be treated as a placeholder only.",
    }
