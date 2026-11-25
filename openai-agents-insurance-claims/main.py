"""Home-insurance claims triage: a triage agent hands off to water, theft and storm specialists."""

import os
import uuid
from pathlib import Path

from dotenv import load_dotenv

# Load the repo-root .env (if present) so OPENAI_API_KEY is available.
load_dotenv(Path(__file__).resolve().parent.parent / ".env")

# Opik reads the project name when the first trace is created, so pin it before
# importing opik: every trace lands in the "openai-agents-insurance-claims" project.
os.environ["OPIK_PROJECT_NAME"] = "openai-agents-insurance-claims"

import opik
from agents import Runner, set_trace_processors, trace
from opik.integrations.openai.agents import OpikTracingProcessor

from claims_agents import triage_agent

# OpikTracingProcessor turns the SDK's own trace events into Opik spans: agent turns
# (general), LLM calls (llm), tool calls (tool) and handoffs. Replacing the processor
# list also stops the SDK from uploading traces to OpenAI's dashboard.
set_trace_processors(processors=[OpikTracingProcessor()])

# Scripted customers: each conversation is a list of turns, no human input needed.
DEMO_CONVERSATIONS = {
    "kitchen-pipe-burst": [
        "Hi, I'm Marta Okafor, policy HP-4410. A pipe burst under my kitchen sink and "
        "the floor is soaked, roughly $6,200 of damage. Is it covered? Please open a claim.",
        "What would I actually receive after the deductible? And send a crew today.",
    ],
    "garage-ebike-theft": [
        "Someone forced my garage door overnight and took a $2,400 e-bike. "
        "Policy HP-7302, please open a claim.",
        "The police report number is PR-55813. Attach it and tell me what I'll be paid.",
    ],
    "roof-shingles-storm": [
        "Last night's storm tore shingles off my roof, about $9,000 of damage. "
        "Policy HP-2288. What's covered?",
        "Book an adjuster for Saturday please.",
    ],
    "basement-groundwater": [
        "Heavy rain pushed groundwater up through my basement floor, about $12,000 "
        "of damage. Policy HP-2288. Open a water claim for me.",
    ],
}


def run_demo() -> None:
    for conversation_id, user_turns in DEMO_CONVERSATIONS.items():
        thread_id = f"{conversation_id}-{uuid.uuid4().hex[:8]}"
        print(f"\n=== {conversation_id} (thread {thread_id}) ===")
        conversation_input: list = []
        # The first turn starts at triage; later turns stay with whichever
        # specialist took over, like a customer staying on the line.
        current_agent = triage_agent
        for user_message in user_turns:
            print(f"\nCustomer: {user_message}")
            conversation_input.append({"role": "user", "content": user_message})
            # One Opik trace per turn. The SDK's group_id becomes the Opik thread_id,
            # so the Threads tab stitches a customer's turns into one conversation.
            with trace(workflow_name="Claims triage", group_id=thread_id):
                result = Runner.run_sync(current_agent, conversation_input)
            print(f"Agent ({result.last_agent.name}): {result.final_output}")
            conversation_input = result.to_input_list()
            current_agent = result.last_agent


if __name__ == "__main__":
    try:
        run_demo()
    finally:
        # Traces are sent from a background thread; flushing makes sure the last
        # turns are delivered before the process exits.
        opik.flush_tracker()
