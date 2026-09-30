from energy_assistant.workflow import route_question


def test_agent_router_selects_forecast_specialist():
    result = route_question("Forecast demand for tomorrow")
    assert result["status"] == "ok"
    assert "forecast" in result["route"]
