"""Command line entry point: `festival plan` and `festival costs`."""

import argparse
from pathlib import Path

from dotenv import load_dotenv

from street_festival.crew import build_crew
from street_festival.data import build_inputs
from street_festival.tracing import enable_tracing, flush


def main(argv: list[str] | None = None) -> None:
    # Find a .env in this folder or any parent (the repo root) before crewai reads the keys.
    for parent in [Path.cwd(), *Path.cwd().parents]:
        if (parent / ".env").exists():
            load_dotenv(parent / ".env")
            break

    parser = argparse.ArgumentParser(prog="festival", description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    plan = sub.add_parser("plan", help="run the three-agent crew once")
    plan.add_argument("--verbose", action="store_true", help="show the crew's reasoning")
    sub.add_parser("costs", help="print tokens and dollar cost per agent for the latest trace")
    args = parser.parse_args(argv)

    if args.command == "plan":
        crew = build_crew(verbose=args.verbose)
        enable_tracing(crew)
        try:
            result = crew.kickoff(inputs=build_inputs())
        finally:
            flush()
        print("\n=== FESTIVAL BUDGET ===\n")
        print(result)

    if args.command == "costs":
        from street_festival.costs import latest_trace_report

        print(latest_trace_report())
