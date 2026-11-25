from street_festival.crew import build_crew


def test_crew_has_three_agents_and_sequential_tasks(monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "test-key-not-real")
    crew = build_crew()
    assert [a.role for a in crew.agents] == ["Logistics Planner", "Vendor Coordinator", "Budget Writer"]
    assert [t.name for t in crew.tasks] == ["Plan the site layout", "Place the vendors", "Write the budget"]
    assert crew.tasks[2].context == [crew.tasks[0], crew.tasks[1]]
