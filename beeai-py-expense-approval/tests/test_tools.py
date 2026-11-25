import asyncio
import json

from expense_agent.data import load_reports
from expense_agent.tools import manager_lookup, manager_lookup_impl, policy_lookup_impl, receipt_check_impl


def test_policy_lookup_known_and_unknown():
    meals = json.loads(policy_lookup_impl(" Meals "))
    assert meals["receipt_required_over_usd"] == 25
    assert "known_categories" in json.loads(policy_lookup_impl("yachts"))


def test_receipt_check_reports_missing_receipt():
    assert json.loads(receipt_check_impl("er-2041"))["on_file"] is True
    assert json.loads(receipt_check_impl("ER-2043"))["on_file"] is False
    assert "error" in json.loads(receipt_check_impl("ER-0000"))


def test_every_scripted_report_has_a_manager_and_receipt_entry():
    for report in load_reports():
        assert "manager" in json.loads(manager_lookup_impl(report["employee"]))
        assert "on_file" in json.loads(receipt_check_impl(report["id"]))


def test_beeai_tool_wrapper_runs_without_any_tracing_configured():
    # The agent calls the @tool-wrapped function; with no tracer provider set, it must behave exactly the same.
    async def call():
        return await manager_lookup.run({"employee": "Lee Brandt"})

    output = asyncio.run(call())
    assert json.loads(output.get_text_content())["manager"] == "Ines Moreau"
