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


def process_document(client: Any, opik_client: Any, doc: dict[str, Any]) -> dict[str, Any]:
    """Run one document through the pipeline, recording every step by hand with the Opik client."""
    text = doc["text"]

    # client.trace() opens the root of the tree: one trace per document, with the raw
    # document as input. Nothing is sent until the batch is flushed.
    trace = opik_client.trace(
        name="redact-document",
        input={"doc_id": doc["id"], "title": doc["title"], "text": text},
        tags=[doc["id"]],
    )

    # trace.span() adds a child of the trace; a "general" span groups the two detectors.
    detect = trace.span(name="detect", type="general", input={"text": text})

    # type="tool": a deterministic helper call, shown with a wrench icon in the tree.
    scan = detect.span(name="regex-scan", type="tool", input={"text": text})
    regex_hits = regex_scan(text)
    scan.end(output={"entities": regex_hits})

    # type="llm" is what makes Opik treat this span as a model call (messages, model, usage).
    llm = detect.span(
        name=f"chat {MODEL}",
        type="llm",
        input={"messages": [{"role": "system", "content": DETECT_PROMPT}, {"role": "user", "content": text}]},
    )
    try:
        llm_hits, response = llm_detect(client, text)
    except Exception as exc:
        # error_info puts a red error badge on the span and the trace instead of a silent gap.
        llm.end(error_info={"exception_type": type(exc).__name__, "message": str(exc), "traceback": ""})
        detect.end()
        trace.end()
        raise
    # model + provider + usage are recorded by hand: this is how Opik computes the dollar
    # cost of the span on the server. Drop the usage dict and the cost column stays empty.
    llm.end(
        output={"entities": llm_hits, "raw": response.choices[0].message.content},
        model=response.model,
        provider="openai",
        usage={
            "prompt_tokens": response.usage.prompt_tokens,
            "completion_tokens": response.usage.completion_tokens,
            "total_tokens": response.usage.total_tokens,
        },
    )
    detect.end(output={"regex": len(regex_hits), "llm": len(llm_hits)})

    classify_span = trace.span(name="classify", type="general", input={"regex": regex_hits, "llm": llm_hits})
    entities = classify(merge_entities(text, regex_hits, llm_hits))
    classify_span.end(output={"entities": entities})

    redact_span = trace.span(name="redact", type="tool", input={"text": text, "entities": entities})
    redacted, mapping = redact(text, entities)
    redact_span.end(output={"redacted": redacted, "mapping": mapping})

    # type="guardrail" marks a check on the output; its pass/fail verdict lives in the span output.
    audit_span = trace.span(
        name="audit", type="guardrail", input={"redacted": redacted, "expected": doc["expected"]}
    )
    report = audit(redacted, entities, doc["expected"])
    audit_span.end(output=report, metadata={"passed": report["leak_free"]})

    # trace.end() closes the root and records the final output shown in the trace list.
    trace.end(output={"redacted": redacted, "leak_free": report["leak_free"]})
    return {"id": doc["id"], "redacted": redacted, "entities": entities, "mapping": mapping, **report}
