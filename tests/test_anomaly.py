from energy_assistant.anomaly import detect


def test_anomaly_detection_returns_flagged_candidates():
    result = detect(limit=5)
    assert "flags" in result
    assert "method" in result
    assert "count" in result
    assert len(result["flags"]) <= 5
