"""Fictional trail data and the PDF generator.

Four invented trails, each with the same four sections (Overview, Hazards,
Permits, Water). The identical layout is deliberate: "Water" of one trail
looks a lot like "Water" of another, so retrieval has to pick the right
trail as well as the right section.

Run directly (`uv run trails.py`) or let main.py call it when docs/ is empty.
"""

import pathlib

from reportlab.lib.pagesizes import LETTER
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer

DOCS_DIR = pathlib.Path(__file__).parent / "docs"

# Section titles, in the order they appear in every guide.
SECTIONS = ["Overview", "Hazards", "Permits", "Water"]

TRAILS: dict[str, dict[str, str]] = {
    "Heron Ridge Loop": {
        "Overview": "Heron Ridge Loop is an 11.4 km circuit starting at the Larch Valley trailhead. "
        "Total elevation gain is 780 m, topping out at 2,115 m on the ridge. Allow 5 to 6 hours.",
        "Hazards": "The north chute below the summit has loose scree, so descend the south side. "
        "The ridge is exposed to lightning; be off it by 2 pm on summer afternoons.",
        "Permits": "A free day permit is required and is issued at the Larch Valley ranger station. "
        "The quota is 40 hikers per day, first come first served.",
        "Water": "Cinder Spring at km 4.2 flows all year and needs no treatment. The tarn at km 8 "
        "is seasonal and dries up by August. There is no water after km 8.",
    },
    "Kestrel Pass Traverse": {
        "Overview": "Kestrel Pass Traverse is a 23.6 km point-to-point route from Dunmoor to Skerry Bay. "
        "Total elevation gain is 1,640 m. Most parties take two days and camp at Lower Kestrel Lake.",
        "Hazards": "Snow bridges persist on the pass until mid-July and can collapse. "
        "The Skerry River crossing at km 9 is knee-deep in early summer; unbuckle your pack straps.",
        "Permits": "An overnight permit costs $18 per party and must be booked online. "
        "Only 12 parties are allowed on the route each night.",
        "Water": "Dunmoor Creek at km 3 is the last reliable stream. Lower Kestrel Lake at km 14 "
        "has water that must be filtered. Between km 3 and km 14 the route is dry.",
    },
    "Old Quarry Trail": {
        "Overview": "Old Quarry Trail is a gentle 6.2 km out-and-back along a former slate quarry. "
        "Total elevation gain is only 310 m. It suits families and takes about 2.5 hours.",
        "Hazards": "The quarry rim is unfenced with sheer 30 m drops, so keep children close. "
        "Ground-nesting wasps are common near the spoil heaps in August.",
        "Permits": "No permit is needed for the Old Quarry Trail. Parking at the trailhead is "
        "limited to 20 cars and is free.",
        "Water": "There is no natural water on the trail. Carry at least 2 litres per person. "
        "A tap at the trailhead picnic area is switched on from May to September.",
    },
    "Marrow Falls Trail": {
        "Overview": "Marrow Falls Trail is an 8.9 km out-and-back to a 40 m waterfall. "
        "Total elevation gain is 540 m. Expect about 4 hours including time at the falls.",
        "Hazards": "The rock behind the falls is permanently wet and very slippery; stay on the "
        "marked platform. The creek can flash-flood after heavy rain upstream.",
        "Permits": "Weekend and holiday visits need a timed-entry pass at $6 per person. "
        "Book at least 48 hours ahead. Weekday visits need no pass.",
        "Water": "Marrow Creek runs alongside the trail at km 2 and km 6. It looks clean "
        "but must be treated before drinking because of grazing upstream.",
    },
}


def generate_all() -> list[pathlib.Path]:
    """Write one PDF per trail into docs/ and return the paths."""
    DOCS_DIR.mkdir(exist_ok=True)
    styles = getSampleStyleSheet()
    paths = []
    for trail, sections in TRAILS.items():
        path = DOCS_DIR / (trail.lower().replace(" ", "-") + ".pdf")
        story = [Paragraph(trail, styles["Title"]), Spacer(1, 0.2 * inch)]
        for title in SECTIONS:
            story.append(Paragraph(title, styles["Heading2"]))
            story.append(Paragraph(sections[title], styles["BodyText"]))
            story.append(Spacer(1, 0.1 * inch))
        SimpleDocTemplate(str(path), pagesize=LETTER, title=trail, author="Trail Guide Press").build(story)
        paths.append(path)
    return paths


if __name__ == "__main__":
    for p in generate_all():
        print(f"wrote {p}")
