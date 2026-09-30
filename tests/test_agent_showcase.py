from energy_assistant.agent_team.specs import AGENT_PROFILES
from energy_assistant.workflow import evaluate_query_routing, route_question


def test_agent_profiles_are_defined():
    assert len(AGENT_PROFILES) >= 5
    names = {agent["name"] for agent in AGENT_PROFILES}
    assert {"Energy Data Analyst", "Anomaly Investigator", "Forecast Specialist", "Insight Synthesizer", "Decision Guide"}.issubset(names)


def test_query_routing_is_explicit_and_supported():
    result = route_question("Which periods show unusual readings?")
    assert result["status"] == "ok"
    assert "anomaly" in result["route"]

    benchmark = evaluate_query_routing()
    assert benchmark["total"] >= 5
    assert benchmark["passed"] >= 4


def test_agent_sections_are_described_in_specs():
    section_names = {agent["name"].lower() for agent in AGENT_PROFILES}
    assert "energy data analyst" in section_names
    assert "anomaly investigator" in section_names
    assert "forecast specialist" in section_names
