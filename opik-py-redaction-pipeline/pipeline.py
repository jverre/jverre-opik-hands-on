"""Document PII redaction: detect -> classify -> redact -> audit."""

from __future__ import annotations

import json
import re
from datetime import datetime
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


def _now() -> datetime:
    return datetime.now().astimezone()


def process_document(client: Any, opik_client: Any, doc: dict[str, Any]) -> dict[str, Any]:
    """Run one document through the pipeline, then record it by hand with the Opik client.

    The work runs first and is timed; the trace and spans are created afterwards, each in a
    single call that already carries its start_time, end_time and output. Opening a span and
    calling .end() a moment later makes the SDK warn about possible data loss (the update can
    overtake the batched create), so each span is written once, complete.
    """
    text = doc["text"]
    t_start = _now()
    error: Exception | None = None
    regex_hits: list[dict[str, str]] = []
    llm_hits: list[dict[str, str]] = []
    response = None
    entities: list[dict[str, str]] = []
    redacted, mapping, report = text, {}, {}
    stamps: dict[str, tuple[datetime, datetime]] = {}

    try:
        a = _now(); regex_hits = regex_scan(text); stamps["regex"] = (a, _now())
        a = _now()
        try:
            llm_hits, response = llm_detect(client, text)
        finally:
            stamps["llm"] = (a, _now())
        a = _now(); entities = classify(merge_entities(text, regex_hits, llm_hits)); stamps["classify"] = (a, _now())
        a = _now(); redacted, mapping = redact(text, entities); stamps["redact"] = (a, _now())
        a = _now(); report = audit(redacted, entities, doc["expected"]); stamps["audit"] = (a, _now())
    except Exception as exc:  # recorded on the trace below, then re-raised
        error = exc

    # client.trace() is the root of the tree: one trace per document, with the raw document
    # as input and the redacted text as output. error_info puts a red badge on a failed run.
    trace = opik_client.trace(
        name="redact-document",
        input={"doc_id": doc["id"], "title": doc["title"], "text": text},
        output={"redacted": redacted, "leak_free": report.get("leak_free")},
        tags=[doc["id"]],
        start_time=t_start,
        end_time=_now(),
        error_info=(
            {"exception_type": type(error).__name__, "message": str(error), "traceback": ""} if error else None
        ),
    )

    # trace.span() adds a child of the trace. "general" is the neutral type, used here to
    # group the two detectors under one "detect" node in the tree.
    detect_start = stamps["regex"][0]
    detect = trace.span(
        name="detect",
        type="general",
        input={"text": text},
        output={"regex": len(regex_hits), "llm": len(llm_hits)},
        start_time=detect_start,
        end_time=stamps.get("llm", stamps["regex"])[1],
    )
    # type="tool": a deterministic helper call, shown as its own row under "detect".
    detect.span(
        name="regex-scan", type="tool", input={"text": text}, output={"entities": regex_hits},
        start_time=stamps["regex"][0], end_time=stamps["regex"][1],
    )
    # type="llm" is what makes Opik treat this span as a model call. model + provider + usage
    # are written by hand: that is how Opik computes the span's dollar cost on the server.
    # Without the usage dict the span still shows, but its cost stays empty.
    detect.span(
        name=f"chat {MODEL}",
        type="llm",
        input={"messages": [{"role": "system", "content": DETECT_PROMPT}, {"role": "user", "content": text}]},
        output={"entities": llm_hits, "raw": response.choices[0].message.content} if response else None,
        model=response.model if response else MODEL,
        provider="openai",
        usage={
            "prompt_tokens": response.usage.prompt_tokens,
            "completion_tokens": response.usage.completion_tokens,
            "total_tokens": response.usage.total_tokens,
        } if response else None,
        start_time=stamps["llm"][0],
        end_time=stamps["llm"][1],
        error_info=(
            {"exception_type": type(error).__name__, "message": str(error), "traceback": ""}
            if error and response is None else None
        ),
    )

    if error:
        opik_client.flush()  # make sure the failed run reaches Opik before we re-raise
        raise error

    trace.span(
        name="classify", type="general", input={"regex": regex_hits, "llm": llm_hits},
        output={"entities": entities}, start_time=stamps["classify"][0], end_time=stamps["classify"][1],
    )
    trace.span(
        name="redact", type="tool", input={"text": text, "entities": entities},
        output={"redacted": redacted, "mapping": mapping},
        start_time=stamps["redact"][0], end_time=stamps["redact"][1],
    )
    # type="guardrail" marks a check on the output. The verdict is in the span output
    # (leak_free, leaked) and in metadata, so failing audits are easy to filter for.
    trace.span(
        name="audit", type="guardrail", input={"redacted": redacted, "expected": doc["expected"]},
        output=report, metadata={"passed": report["leak_free"]},
        start_time=stamps["audit"][0], end_time=stamps["audit"][1],
    )

    # Feedback scores attach to the trace: they become sortable columns in the trace table
    # and are averaged per project. The reason shows on hover.
    leaked_reason = f"leaked: {report['leaked']}" if report["leaked"] else "nothing left in the output"
    trace.log_feedback_score(name="leak_free", value=1.0 if report["leak_free"] else 0.0, reason=leaked_reason)
    trace.log_feedback_score(name="recall", value=report["recall"], reason="share of planted PII removed")
    trace.log_feedback_score(name="precision", value=report["precision"], reason="share of detections that were real PII")
    return {"id": doc["id"], "redacted": redacted, "entities": entities, "mapping": mapping, **report}
