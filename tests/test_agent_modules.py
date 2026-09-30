import importlib


def test_guardrail_modules_exist():
    for name in [
        "energy_assistant.guardrails.data_scope_guardrail",
        "energy_assistant.guardrails.request_scope_guardrail",
        "energy_assistant.guardrails.context_guardrail",
    ]:
        module = importlib.import_module(name)
        assert hasattr(module, "evaluate") or hasattr(module, "guard") or hasattr(module, "check")


def test_agent_modules_exist():
    for name in [
        "energy_assistant.agent_team.data_analyst_agent",
        "energy_assistant.agent_team.anomaly_investigator_agent",
        "energy_assistant.agent_team.forecast_specialist_agent",
        "energy_assistant.agent_team.insight_synthesizer_agent",
        "energy_assistant.agent_team.decision_guide_agent",
    ]:
        module = importlib.import_module(name)
        assert module is not None


def test_fallback_module_exists():
    module = importlib.import_module("energy_assistant.fallbacks.forecast_strategy")
    assert hasattr(module, "choose_forecast_strategy")
