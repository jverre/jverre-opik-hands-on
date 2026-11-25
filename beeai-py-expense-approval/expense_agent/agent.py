"""The triage agent: a BeeAI ReAct agent on gpt-4o-mini with three lookup tools."""
from beeai_framework.agents.react import ReActAgent
from beeai_framework.backend import ChatModel
from beeai_framework.memory import TokenMemory

from expense_agent.decision import Decision, parse_decision
from expense_agent.tools import ALL_TOOLS, CATEGORIES

INSTRUCTIONS = f"""You are the first-pass expense reviewer at Harbor & Pine Outfitters.

For the expense report below, do these things in order:
1. Call policy_lookup for the report's category (one of: {", ".join(CATEGORIES)}).
2. Call receipt_check with the report id.
3. Call manager_lookup for the employee.
Never state a limit, a receipt status or a manager from memory; use what the tools returned.

Then decide: "approve" when the amount is within policy and the receipt rule is met,
"needs_manager" when something is over a limit or missing but fixable by the manager,
"reject" when policy forbids the expense outright.

Format your final answer exactly like this:
Decision: <approve | needs_manager | reject>
Reason: <one or two sentences citing the policy and receipt facts>
Approver: <manager name and email, or "none">
Message: <2-3 friendly sentences to the employee about what happens next>"""


def build_agent() -> ReActAgent:
    llm = ChatModel.from_name("openai:gpt-4o-mini")
    # Fresh memory per agent: each report is an independent run.
    return ReActAgent(llm=llm, tools=ALL_TOOLS, memory=TokenMemory(llm))


def format_report(report: dict) -> str:
    return (
        f"Report {report['id']} from {report['employee']}\n"
        f"Category: {report['category']}\nAmount: USD {report['amount_usd']:.2f}\n"
        f"Description: {report['description']}"
    )


async def review_report(report: dict) -> tuple[str, Decision]:
    agent = build_agent()
    result = await agent.run(
        f"{INSTRUCTIONS}\n\n{format_report(report)}",
        max_retries_per_step=3,
        total_max_retries=10,
        max_iterations=8,
    )
    text = result.last_message.text
    return text, parse_decision(text)
