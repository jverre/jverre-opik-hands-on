"""Command line: `uv run tasting extract|batch`."""

import argparse
import json
import sys

from tasting.config import load_env


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


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="tasting", description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)

    one = sub.add_parser("extract", help="extract one note")
    one.add_argument("text", nargs="?", help="the raw note")
    one.add_argument("--id", help="use a bundled note by id instead of text")
    one.set_defaults(func=_extract)

    sub.add_parser("batch", help="extract every bundled note").set_defaults(func=_batch)
    return parser


def main() -> None:
    load_env()
    args = build_parser().parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
