from claims_agents import theft_agent, triage_agent, water_agent


def test_triage_hands_off_to_three_specialists():
    names = {agent.name for agent in triage_agent.handoffs}
    assert names == {"Water Damage Agent", "Theft Agent", "Storm Damage Agent"}


def test_specialists_only_get_their_own_special_tools():
    water_tools = {t.name for t in water_agent.tools}
    theft_tools = {t.name for t in theft_agent.tools}
    assert "request_mitigation_crew" in water_tools - theft_tools
    assert "attach_police_report" in theft_tools - water_tools
