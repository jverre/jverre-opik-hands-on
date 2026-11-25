"""Opik wiring: everything that makes a crew run visible lives here."""

import opik
from crewai import Crew
from opik.integrations.crewai import track_crewai

# The Opik project every trace lands in. Without a name they go to "Default Project".
PROJECT_NAME = "crewai-street-festival-planner"


def enable_tracing(crew: Crew) -> None:
    # track_crewai patches Crew.kickoff, Task.execute_sync, Agent.execute_task and the LLM clients.
    # One kickoff becomes one trace; tasks and agents are nested general spans; each completion is
    # an llm span with model, token usage and cost. Passing `crew` is required on CrewAI 1.x,
    # otherwise the LLM calls are not patched and the trace has no token or cost data.
    track_crewai(project_name=PROJECT_NAME, crew=crew)


def flush() -> None:
    # Traces are sent from a background thread; a short CLI run exits before they upload
    # unless we flush, and the trace then never appears in Opik.
    opik.flush_tracker()
