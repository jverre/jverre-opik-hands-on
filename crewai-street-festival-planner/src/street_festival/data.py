"""Load the offline festival files and render them as prompt text."""

import csv
import json
from dataclasses import dataclass
from pathlib import Path

DATA_DIR = Path(__file__).resolve().parents[2] / "data"


@dataclass(frozen=True)
class Vendor:
    name: str
    category: str
    quote_usd: int
    power_amps: int
    notes: str


def load_site(data_dir: Path = DATA_DIR) -> dict:
    return json.loads((data_dir / "site.json").read_text())


def load_vendors(data_dir: Path = DATA_DIR) -> list[Vendor]:
    with (data_dir / "vendors.csv").open(newline="") as f:
        return [
            Vendor(r["name"], r["category"], int(r["quote_usd"]), int(r["power_amps"]), r["notes"])
            for r in csv.DictReader(f)
        ]


def load_rules(data_dir: Path = DATA_DIR) -> str:
    return (data_dir / "city_rules.md").read_text()


def total_quotes(vendors: list[Vendor]) -> int:
    return sum(v.quote_usd for v in vendors)


def render_site(site: dict) -> str:
    lines = [
        f"{site['festival']} - {site['date']}",
        f"Expected attendance: {site['expected_attendance']}",
        f"Budget cap: ${site['budget_cap_usd']:,}",
        "Closed streets: " + "; ".join(site["closed_streets"]),
        "Zones:",
    ]
    for z in site["zones"]:
        lines.append(f"- {z['name']} ({z['location']}): capacity {z['capacity']}, {z['power_amps']} A")
    lines.append("Constraints:")
    lines.extend(f"- {c}" for c in site["constraints"])
    return "\n".join(lines)


def render_vendors(vendors: list[Vendor]) -> str:
    rows = ["name | category | quote | amps | notes"]
    rows += [f"{v.name} | {v.category} | ${v.quote_usd} | {v.power_amps} A | {v.notes}" for v in vendors]
    rows.append(f"All quotes together: ${total_quotes(vendors):,}")
    return "\n".join(rows)


def build_inputs(data_dir: Path = DATA_DIR) -> dict[str, str]:
    """The three template variables the crew's tasks interpolate."""
    return {
        "site": render_site(load_site(data_dir)),
        "vendors": render_vendors(load_vendors(data_dir)),
        "rules": load_rules(data_dir),
    }
