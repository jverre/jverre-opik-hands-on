"""Home-insurance claims triage: a triage agent hands off to water, theft and storm specialists."""

import uuid
from pathlib import Path

from dotenv import load_dotenv

# Load the repo-root .env (if present) so OPENAI_API_KEY is available.
load_dotenv(Path(__file__).resolve().parent.parent / ".env")

from agents import Runner, trace

from claims_agents import triage_agent

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
        for user_message in user_turns:
            print(f"\nCustomer: {user_message}")
            conversation_input.append({"role": "user", "content": user_message})
            # One trace per turn, all turns of a conversation share a group_id.
            with trace(workflow_name="Claims triage", group_id=thread_id):
                result = Runner.run_sync(triage_agent, conversation_input)
            print(f"Agent ({result.last_agent.name}): {result.final_output}")
            conversation_input = result.to_input_list()


if __name__ == "__main__":
    run_demo()
