"""Runs the three scripted expense reports through the agent. `uv run main.py`."""
import asyncio
import os
from pathlib import Path

from dotenv import load_dotenv

# Load this folder's .env first, then fall back to the repo-root .env.
load_dotenv(Path(__file__).parent / ".env")
load_dotenv(Path(__file__).parent.parent / ".env")
# Some dev machines route OpenAI traffic through a local proxy via this variable.
os.environ.pop("OPENAI_BASE_URL", None)

from expense_agent.data import load_reports  # noqa: E402
from expense_agent.tracing import flush_tracing, setup_tracing  # noqa: E402


async def main() -> None:
    if not os.environ.get("OPENAI_API_KEY"):
        raise SystemExit("Missing OPENAI_API_KEY. Copy .env.example to .env and fill it in.")
    # Tracing must be live before the agent runs so every span is captured.
    provider = setup_tracing()
    from expense_agent.agent import format_report, review_report

    for report in load_reports():
        print(f"\n=== {report['id']} ===\n{format_report(report)}")
        text, decision = await review_report(report)
        print(f"\nAgent answer:\n{text}\n-> verdict: {decision.verdict}")
    flush_tracing(provider)  # push the last spans to Opik before exiting
    print("\nDone. Open the beeai-py-expense-approval project in Opik to see the traces.")


if __name__ == "__main__":
    asyncio.run(main())
