"""The section-level test suite: questions, expected sections, and helpers.

Every item names the trail and section whose text holds the answer. Two kinds
of check use that: the LLM judge reads plain-language assertions (the answer
states the fact; retrieval surfaced the right section), and `section_hit` is a
plain-Python check printed next to the suite result.
"""

SUITE_NAME = "trail-guide-sections"

# (question, expected trail, expected section, assertions about the answer)
ITEMS = [
    (
        "How much elevation do I gain on Heron Ridge Loop?",
        "Heron Ridge Loop", "Overview",
        ["The answer states the elevation gain is 780 m"],
    ),
    (
        "What are the dangers on the Kestrel Pass Traverse?",
        "Kestrel Pass Traverse", "Hazards",
        ["The answer mentions snow bridges that persist until mid-July",
         "The answer mentions the knee-deep Skerry River crossing at km 9"],
    ),
    (
        "Do I need a permit for Kestrel Pass Traverse, and what does it cost?",
        "Kestrel Pass Traverse", "Permits",
        ["The answer states an overnight permit costs $18 per party"],
    ),
    (
        "How many hikers per day does Heron Ridge Loop allow?",
        "Heron Ridge Loop", "Permits",
        ["The answer states the quota is 40 hikers per day"],
    ),
    (
        "Where can I get drinking water on Marrow Falls Trail?",
        "Marrow Falls Trail", "Water",
        ["The answer says Marrow Creek is available at km 2 and km 6",
         "The answer says the water must be treated before drinking"],
    ),
    (
        "Is there any water on the Old Quarry Trail?",
        "Old Quarry Trail", "Water",
        ["The answer says there is no natural water on the trail",
         "The answer says to carry at least 2 litres per person"],
    ),
    (
        "When is the weekend pass needed for Marrow Falls and how far ahead do I book?",
        "Marrow Falls Trail", "Permits",
        ["The answer states the pass is needed on weekends and holidays and must be "
         "booked at least 48 hours ahead"],
    ),
    (
        "How long is Old Quarry Trail?",
        "Old Quarry Trail", "Overview",
        ["The answer states the trail is 6.2 km"],
    ),
]

GLOBAL_ASSERTIONS = [
    "Every distance, elevation, fee, quota and date in the answer appears in "
    "retrieved_excerpts - the answer invents no figures",
    "The answer is about the trail named in the question, not a different trail",
]


def section_label(trail: str, section: str) -> str:
    return f"{trail} / {section}"


def section_hit(retrieved: list[str], trail: str, section: str) -> bool:
    """True when the expected trail+section is among the retrieved sections."""
    return section_label(trail, section) in retrieved


def suite_rows() -> list[dict]:
    """Items shaped for `suite.insert`: question + expected section as data, assertions per item."""
    return [
        {
            "data": {
                "question": q,
                "expected_section": section_label(trail, section),
            },
            "assertions": assertions
            + [f"retrieved_sections includes '{section_label(trail, section)}'"],
        }
        for q, trail, section, assertions in ITEMS
    ]
