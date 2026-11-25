"""The three tools the agent can call. Plain functions over canned data, so only the LLM call leaves the machine."""
import json

from beeai_framework.tools import tool

from expense_agent.data import load_employees, load_policy, load_receipts

CATEGORIES = list(load_policy())


def policy_lookup_impl(category: str) -> str:
    policy = load_policy().get(category.strip().lower())
    if policy is None:
        return json.dumps({"error": f"unknown category '{category}'", "known_categories": CATEGORIES})
    return json.dumps({"category": category.strip().lower(), **policy})


def receipt_check_impl(report_id: str) -> str:
    receipt = load_receipts().get(report_id.strip().upper())
    if receipt is None:
        return json.dumps({"error": f"no report with id '{report_id}'"})
    return json.dumps({"report_id": report_id.strip().upper(), **receipt})


def manager_lookup_impl(employee: str) -> str:
    entry = load_employees().get(employee.strip())
    if entry is None:
        return json.dumps({"error": f"no employee named '{employee}'"})
    return json.dumps({"employee": employee.strip(), **entry})


@tool(name="policy_lookup")
def policy_lookup(category: str) -> str:
    """Look up the reimbursement policy for an expense category (meals, lodging, airfare, ground_transport, software). Returns the limit, receipt threshold and notes."""
    return policy_lookup_impl(category)


@tool(name="receipt_check")
def receipt_check(report_id: str) -> str:
    """Check whether a receipt is on file for an expense report id such as ER-2041. Returns vendor, itemised lines and notes."""
    return receipt_check_impl(report_id)


@tool(name="manager_lookup")
def manager_lookup(employee: str) -> str:
    """Find the approving manager, their email and their approval limit in USD for an employee, by full name."""
    return manager_lookup_impl(employee)


ALL_TOOLS = [policy_lookup, receipt_check, manager_lookup]
