from energy_assistant.fallbacks.forecast_strategy import choose_forecast_strategy


def test_forecast_strategy_prefers_weekly_history():
    result = choose_forecast_strategy(200, True, True)
    assert result["model"] == "Weekly seasonal-naive"
    assert result["fallback_used"] is False


def test_forecast_strategy_uses_safe_fallback_for_short_history():
    result = choose_forecast_strategy(12, False, False)
    assert result["model"] == "Insufficient-history fallback"
    assert result["fallback_used"] is True
