"""Command line: `uv run tasting extract|batch|suite`."""

import argparse
import json
import sys

from tasting.config import load_env
from tasting.telemetry import flush_tracing, setup_tracing


def _extract(args: argparse.Namespace) -> None:
    from tasting.agent import extract_note
    from tasting.corpus import get_note

    text = get_note(args.id)["text"] if args.id else args.text
    if not text:
        sys.exit("give a note as text, or --id <note id> (see `tasting batch`)")
    print(json.dumps(extract_note(text), indent=2))


def _batch(_: argparse.Namespace) -> None:
    from tasting.agent import extract_note
    from tasting.corpus import load_notes

    for note in load_notes():
        print(f"[{note['id']}] {note['text']}")
        print(f"  -> {json.dumps(extract_note(note['text']))}\n")


def _suite(_: argparse.Namespace) -> None:
    from tasting.suite import run_suite

    result = run_suite()
    print(f"\nPass rate: {result.pass_rate:.0%} ({result.items_passed}/{result.items_total} items)")
    for item_result in result.item_results.values():
        text = item_result.test_results[0].test_case.task_output["input"]["text"]
        print(f"  [{'PASS' if item_result.passed else 'FAIL'}] {text[:60]!r}")
    print(f"\nExperiment: {result.experiment_name} ({result.experiment_url})")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="tasting", description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)

    one = sub.add_parser("extract", help="extract one note")
    one.add_argument("text", nargs="?", help="the raw note")
    one.add_argument("--id", help="use a bundled note by id instead of text")
    one.set_defaults(func=_extract)

    sub.add_parser("batch", help="extract every bundled note").set_defaults(func=_batch)
    sub.add_parser("suite", help="run the Opik test suite").set_defaults(func=_suite)
    return parser


def main() -> None:
    load_env()
    args = build_parser().parse_args()
    setup_tracing()  # must run before any agent is built, so its spans are exported
    try:
        args.func(args)
    finally:
        flush_tracing()  # without it a short-lived CLI can exit with spans still buffered


if __name__ == "__main__":
    main()
