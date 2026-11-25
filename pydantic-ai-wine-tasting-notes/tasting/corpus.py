"""Loads the fictional sommelier notes shipped in data/notes.json."""

import json
from typing import TypedDict

from tasting.config import NOTES_FILE


class Note(TypedDict):
    id: str
    text: str


def load_notes() -> list[Note]:
    return json.loads(NOTES_FILE.read_text())


def get_note(note_id: str) -> Note:
    for note in load_notes():
        if note["id"] == note_id:
            return note
    raise KeyError(f"unknown note id {note_id!r}")
