from energy_assistant.api import app


def test_api_exposes_core_service_routes():
    paths = {route.path for route in app.routes if hasattr(route, "path")}
    assert {"/health", "/ready", "/api/summary", "/api/anomalies", "/api/forecast", "/api/ask", "/api/evaluation"}.issubset(paths)
