"""The three review steps. Each one runs as a Temporal activity inside the worker."""

import json

from temporalio import activity

from . import llm
from .budget import check_budget as run_budget_check
from .config import get_application, load_rules

ELIGIBILITY_SYSTEM = (
    "You screen small-grant applications against the fund's rules. "
    'Reply with JSON: {"eligible": true|false, "reasons": [short strings]}.'
)
SUMMARY_SYSTEM = (
    "You write a three-sentence briefing for a grant reviewer: what is being asked, "
    "whether eligibility and budget checks passed, and a recommendation (fund, fund with "
    "conditions, or decline)."
)


@activity.defn
async def check_eligibility(app_id: str) -> dict:
    app = get_application(app_id)
    user = f"RULES:\n{load_rules()}\nAPPLICATION:\n{json.dumps(app, indent=2)}"
    result, _ = await llm.chat_json("eligibility-check", ELIGIBILITY_SYSTEM, user)
    return {"eligible": bool(result.get("eligible")), "reasons": result.get("reasons", [])}


@activity.defn
async def check_budget(app_id: str) -> dict:
    # Stand-in for a call to a flaky finance service: the first attempt of every
    # workflow fails, Temporal retries, the second attempt succeeds.
    if activity.info().attempt == 1:
        raise RuntimeError("Finance ledger service unavailable (503)")
    return run_budget_check(get_application(app_id))


@activity.defn
async def write_reviewer_summary(app_id: str, eligibility: dict, budget: dict) -> str:
    app = get_application(app_id)
    user = json.dumps(
        {"application": app, "eligibility": eligibility, "budget": budget}, indent=2
    )
    text, _ = await llm.chat_text("reviewer-summary", SUMMARY_SYSTEM, user)
    return text
