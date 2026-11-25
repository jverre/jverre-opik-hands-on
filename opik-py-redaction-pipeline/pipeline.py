"""Document PII redaction: detect -> classify -> redact -> audit."""

from __future__ import annotations

import json
import re
from typing import Any

MODEL = "gpt-4o-mini"

# Deterministic patterns: cheap, exact, and the safety net under the model.
PATTERNS: dict[str, re.Pattern[str]] = {
    "EMAIL": re.compile(r"[\w.+-]+@[\w-]+\.[\w.]+"),
    "SSN": re.compile(r"\b\d{3}-\d{2}-\d{4}\b"),
    "CARD": re.compile(r"\b(?:\d{4}[ -]){3}\d{4}\b"),
    "PHONE": re.compile(r"(?:\+\d{1,2}\s)?(?:\(\d{3}\)\s?|\d{3}[-.\s])\d{3}[-.\s]\d{4}"),
}

# type -> (category, severity)
TAXONOMY: dict[str, tuple[str, str]] = {
    "SSN": ("government_id", "high"),
    "CARD": ("financial", "high"),
    "MEMBER_ID": ("government_id", "high"),
    "PERSON": ("direct_identifier", "medium"),
    "EMAIL": ("contact", "medium"),
    "PHONE": ("contact", "medium"),
    "ADDRESS": ("contact", "medium"),
    "DOB": ("demographic", "medium"),
}

DETECT_PROMPT = (
    "You find personal data in a document. Return JSON of the form "
    '{"entities": [{"text": "<exact substring>", "type": "<TYPE>"}]}. '
    "TYPE is one of PERSON, ADDRESS, DOB, MEMBER_ID, EMAIL, PHONE, SSN, CARD. "
    "Copy each text exactly as written. Real people and street addresses only: "
    "never company names, products, or job titles. Return every distinct "
    "occurrence form once (a first name used alone is its own entity)."
)


def regex_scan(text: str) -> list[dict[str, str]]:
    """Find structured identifiers with regular expressions."""
    found = []
    for etype, pattern in PATTERNS.items():
        for match in pattern.finditer(text):
            found.append({"text": match.group(0), "type": etype, "source": "regex"})
    return found


def parse_entities(raw: str) -> list[dict[str, str]]:
    """Parse the model's JSON reply; a malformed reply yields no entities."""
    try:
        items = json.loads(raw).get("entities", [])
    except (json.JSONDecodeError, AttributeError):
        return []
    out = []
    for item in items:
        if isinstance(item, dict) and item.get("text") and item.get("type") in TAXONOMY:
            out.append({"text": str(item["text"]), "type": item["type"], "source": "llm"})
    return out


def llm_detect(client: Any, text: str) -> tuple[list[dict[str, str]], Any]:
    """Ask the model for names, addresses and the like. Returns (entities, raw response)."""
    response = client.chat.completions.create(
        model=MODEL,
        temperature=0,
        response_format={"type": "json_object"},
        messages=[
            {"role": "system", "content": DETECT_PROMPT},
            {"role": "user", "content": text},
        ],
    )
    return parse_entities(response.choices[0].message.content or ""), response


def merge_entities(text: str, *groups: list[dict[str, str]]) -> list[dict[str, str]]:
    """Union the detectors. Drop anything not literally in the text (hallucinations)."""
    merged: dict[str, dict[str, str]] = {}
    for group in groups:
        for ent in group:
            if ent["text"] in text and ent["text"] not in merged:
                merged[ent["text"]] = ent
    return list(merged.values())


def classify(entities: list[dict[str, str]]) -> list[dict[str, str]]:
    """Attach a category and a severity to every entity."""
    return [
        {**e, "category": TAXONOMY[e["type"]][0], "severity": TAXONOMY[e["type"]][1]}
        for e in entities
    ]


def redact(text: str, entities: list[dict[str, str]]) -> tuple[str, dict[str, str]]:
    """Replace each entity with a stable placeholder such as [PERSON_1]."""
    counters: dict[str, int] = {}
    mapping: dict[str, str] = {}
    redacted = text
    # Longest first, so "Marisol Venkataraman" goes before "Marisol".
    for ent in sorted(entities, key=lambda e: len(e["text"]), reverse=True):
        counters[ent["type"]] = counters.get(ent["type"], 0) + 1
        placeholder = f"[{ent['type']}_{counters[ent['type']]}]"
        mapping[ent["text"]] = placeholder
        redacted = redacted.replace(ent["text"], placeholder)
    return redacted, mapping


def audit(redacted: str, entities: list[dict[str, str]], expected: list[str]) -> dict[str, Any]:
    """Check the output: nothing detected or expected may survive in the redacted text."""
    low = redacted.lower()
    leaked = sorted({s for s in [e["text"] for e in entities] + expected if s.lower() in low})
    residual = [m["text"] for m in regex_scan(redacted)]
    caught = [s for s in expected if s.lower() not in low]
    recall = len(caught) / len(expected) if expected else 1.0
    detected = [e["text"].lower() for e in entities]
    if detected:
        hits = [d for d in detected if any(d in x.lower() or x.lower() in d for x in expected)]
        precision = len(hits) / len(detected)
    else:
        precision = 1.0 if not expected else 0.0
    return {
        "leaked": leaked + residual,
        "leak_free": not leaked and not residual,
        "recall": round(recall, 3),
        "precision": round(precision, 3),
    }


def process_document(client: Any, doc: dict[str, Any]) -> dict[str, Any]:
    text = doc["text"]
    regex_hits = regex_scan(text)
    llm_hits, _response = llm_detect(client, text)
    entities = classify(merge_entities(text, regex_hits, llm_hits))
    redacted, mapping = redact(text, entities)
    report = audit(redacted, entities, doc["expected"])
    return {"id": doc["id"], "redacted": redacted, "entities": entities, "mapping": mapping, **report}
