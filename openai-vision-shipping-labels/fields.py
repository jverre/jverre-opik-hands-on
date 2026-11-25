"""Pure helpers: the extraction schema, the prompt, and output normalisation.

No model calls and no Opik in here, so everything is unit-testable offline.
"""

import json
import re
from typing import Any

SYSTEM_PROMPT = """\
You read photos of parcel shipping labels and extract six fields. Report only
what is actually on the label; if a character is smudged or unreadable, give
your best reading rather than leaving the field out. The label may be rotated.

- tracking_number: the human-readable tracking code printed on the label,
  exactly as shown (not the barcode bars).
- carrier: the carrier name in the header.
- service_level: the service tier shown on the label (Ground, Express, ...).
- sender_postcode: the postcode of the sender / shipper / FROM block.
- recipient_postcode: the postcode of the recipient / consignee / TO block.
- weight_kg: the parcel weight in kilograms, as a number. If the label prints
  pounds, convert to kilograms (1 lb = 0.4536 kg)."""

FIELDS_SCHEMA = {
    "type": "object",
    "properties": {
        "tracking_number": {"type": "string"},
        "carrier": {"type": "string"},
        "service_level": {"type": "string"},
        "sender_postcode": {"type": "string"},
        "recipient_postcode": {"type": "string"},
        "weight_kg": {"type": "number"},
    },
    "required": ["tracking_number", "carrier", "service_level", "sender_postcode",
                 "recipient_postcode", "weight_kg"],
    "additionalProperties": False,
}


def normalize_tracking(value: str) -> str:
    """'sp 4821-7730 19' -> 'SP4821773019': drop spaces and hyphens, upper-case."""
    return re.sub(r"[\s\-]", "", value).upper()


def normalize_postcode(value: str) -> str:
    """Upper-case and collapse whitespace: ' sw1a  1aa ' -> 'SW1A 1AA'."""
    return re.sub(r"\s+", " ", value.strip()).upper()


def parse_fields(raw_json: str) -> dict[str, Any]:
    """Parse the model's JSON and normalise it into the shape the suite judges."""
    data = json.loads(raw_json)
    return {
        "tracking_number": normalize_tracking(data["tracking_number"]),
        "carrier": data["carrier"].strip(),
        "service_level": data["service_level"].strip(),
        "sender_postcode": normalize_postcode(data["sender_postcode"]),
        "recipient_postcode": normalize_postcode(data["recipient_postcode"]),
        "weight_kg": round(float(data["weight_kg"]), 2),
    }
