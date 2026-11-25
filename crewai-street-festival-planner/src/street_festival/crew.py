"""The crew: a logistics planner, a vendor coordinator and a budget writer."""

from crewai import Agent, Crew, Process, Task

MODEL = "gpt-4o-mini"


def build_crew(model: str = MODEL, verbose: bool = False) -> Crew:
    logistics = Agent(
        role="Logistics Planner",
        goal="Lay out the closures, zones, marshals and toilets so the festival is safe.",
        backstory="A city events officer who has closed forty streets and cites the permit rules by number.",
        llm=model,
    )
    vendors = Agent(
        role="Vendor Coordinator",
        goal="Place every vendor in a zone without breaking power or permit limits.",
        backstory="A market manager who has seen every extension-cord disaster and plans around amps first.",
        llm=model,
    )
    writer = Agent(
        role="Budget Writer",
        goal="Turn the plan and the vendor quotes into a budget the committee can approve.",
        backstory="A treasurer who writes short, exact budgets and flags any overspend in the first line.",
        llm=model,
    )

    layout_task = Task(
        name="Plan the site layout",
        description=(
            "Using ONLY the data below, plan the logistics: marshal count, toilet count "
            "(with accessible units), and what must happen before 09:00.\n\n"
            "SITE:\n{site}\n\nCITY RULES:\n{rules}"
        ),
        expected_output="6-8 bullets, each with a number and the rule or constraint it satisfies.",
        agent=logistics,
    )
    placement_task = Task(
        name="Place the vendors",
        description=(
            "Assign each vendor to a zone, respecting the amps each zone has and the city rules. "
            "Name any vendor you would drop and why.\n\nVENDORS:\n{vendors}\n\nSITE:\n{site}\n\n"
            "CITY RULES:\n{rules}"
        ),
        expected_output="A zone-by-zone list of vendors with total amps per zone, then a short list of problems.",
        agent=vendors,
        context=[layout_task],
    )
    budget_task = Task(
        name="Write the budget",
        description=(
            "Write the festival budget from the vendor quotes and the logistics plan. "
            "State the total against the budget cap and the required contingency reserve."
        ),
        expected_output="Under 250 words: a line-item table by category, total, cap, reserve, and one recommendation.",
        agent=writer,
        context=[layout_task, placement_task],
    )

    return Crew(
        agents=[logistics, vendors, writer],
        tasks=[layout_task, placement_task, budget_task],
        process=Process.sequential,
        verbose=verbose,
    )
