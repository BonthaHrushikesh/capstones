from energy_assistant import analytics


def test_summary_returns_peak_and_energy_fields():
    result = analytics.summary()
    assert result["mean_kw"] > 0
    assert result["max_kw"] > 0
    assert "total_energy_kwh" in result
    assert "peak_hours" in result
    assert result["max_at"].endswith("00:00:00") or "T" in result["max_at"]
