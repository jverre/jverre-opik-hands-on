"""Triage agent plus three specialists, wired to the claims desk through function tools."""

import json

from agents import Agent, function_tool

from claims_desk import ClaimsDesk

MODEL = "gpt-4o-mini"

# One shared desk per process: claims opened in one turn are visible in the next.
desk = ClaimsDesk.from_files()


@function_tool
def check_coverage(policy_id: str, peril: str) -> str:
    """Look up whether a policy covers a peril. Perils: sudden_water, flood, theft, wind_hail."""
    return json.dumps(desk.check_coverage(policy_id, peril))


@function_tool
def estimate_payout(policy_id: str, peril: str, loss_usd: float) -> str:
    """Estimate the payout for a loss after the policy limit and deductible."""
    return json.dumps(desk.estimate_payout(policy_id, peril, loss_usd))


@function_tool
def open_claim(policy_id: str, peril: str, summary: str, loss_usd: float) -> str:
    """Open a claim for a covered peril. Returns the new claim id."""
    return json.dumps(desk.open_claim(policy_id, peril, summary, loss_usd))


@function_tool
def get_claim_status(claim_id: str) -> str:
    """Return the current status of a claim."""
    return json.dumps(desk.get_claim_status(claim_id))


@function_tool
def request_mitigation_crew(claim_id: str) -> str:
    """Dispatch an emergency water-mitigation crew to a water claim."""
    return json.dumps(desk.request_mitigation_crew(claim_id))


@function_tool
def attach_police_report(claim_id: str, report_number: str) -> str:
    """Attach a police report number to a theft claim."""
    return json.dumps(desk.attach_police_report(claim_id, report_number))


@function_tool
def book_adjuster(claim_id: str, visit_day: str) -> str:
    """Book an on-site adjuster visit for a claim on the given day."""
    return json.dumps(desk.book_adjuster(claim_id, visit_day))


COMMON_RULES = (
    "Always call check_coverage before promising anything, and never invent coverage. "
    "If the peril is excluded, say so plainly and do not open a claim. "
    "Quote amounts from tool results only. Keep replies to three sentences."
)

water_agent = Agent(
    name="Water Damage Agent",
    handoff_description="Burst pipes, leaks, appliance overflows, flooding and other water damage.",
    instructions=(
        "You handle water damage claims for a home insurer. Classify the loss as "
        "sudden_water (burst pipe, leaking appliance) or flood (rising groundwater, "
        "surface water, sewer backup). " + COMMON_RULES
    ),
    model=MODEL,
    tools=[check_coverage, estimate_payout, open_claim, get_claim_status,
           request_mitigation_crew],
)

theft_agent = Agent(
    name="Theft Agent",
    handoff_description="Burglary, break-ins and stolen belongings.",
    instructions=(
        "You handle theft and burglary claims for a home insurer. Use the peril "
        "theft. Attach a police report only when the customer gives a report number. "
        + COMMON_RULES
    ),
    model=MODEL,
    tools=[check_coverage, estimate_payout, open_claim, get_claim_status,
           attach_police_report],
)

storm_agent = Agent(
    name="Storm Damage Agent",
    handoff_description="Wind, hail, fallen trees and other storm damage to the structure.",
    instructions=(
        "You handle storm damage claims for a home insurer. Use the peril wind_hail. "
        "Book an adjuster only when the customer names a day. " + COMMON_RULES
    ),
    model=MODEL,
    tools=[check_coverage, estimate_payout, open_claim, get_claim_status, book_adjuster],
)

triage_agent = Agent(
    name="Claims Triage Agent",
    instructions=(
        "You are the first point of contact for a home-insurance claims line. "
        "Decide whether the customer's loss is water damage, theft, or storm damage "
        "and hand off to that specialist immediately. Do not answer coverage questions "
        "yourself. If water arrived because of a storm, choose the water specialist."
    ),
    model=MODEL,
    handoffs=[water_agent, theft_agent, storm_agent],
)
