"""Offline tests: no provider keys, no Opik server (run with OPIK_TRACK_DISABLE=true)."""

import sys
from pathlib import Path
from types import SimpleNamespace

sys.path.insert(0, str(Path(__file__).parents[1]))

import suite
import trails
from main import retrieved_sections, split_sections


def guide_text(trail: str) -> str:
    body = "\n".join(f"{s}\n{trails.TRAILS[trail][s]}" for s in trails.SECTIONS)
    return f"{trail}\n{body}"


def test_split_gives_one_tagged_node_per_section():
    nodes = split_sections("Heron Ridge Loop", guide_text("Heron Ridge Loop"))
    assert [n.metadata["section"] for n in nodes] == trails.SECTIONS
    assert all(n.metadata["trail"] == "Heron Ridge Loop" for n in nodes)
    assert "780 m" in nodes[0].text and nodes[0].text.startswith("Heron Ridge Loop - Overview")


def test_every_suite_item_points_at_a_real_section():
    for _, trail, section, _ in suite.ITEMS:
        assert section in trails.TRAILS[trail]


def test_suite_rows_carry_a_retrieval_assertion():
    rows = suite.suite_rows()
    assert len(rows) == len(suite.ITEMS)
    for row in rows:
        label = row["data"]["expected_section"]
        assert any(label in a for a in row["assertions"])


def test_section_hit():
    got = ["Old Quarry Trail / Water", "Marrow Falls Trail / Water"]
    assert suite.section_hit(got, "Marrow Falls Trail", "Water")
    assert not suite.section_hit(got, "Marrow Falls Trail", "Permits")


def test_retrieved_sections_with_stubbed_response():
    node = lambda t, s: SimpleNamespace(node=SimpleNamespace(metadata={"trail": t, "section": s}))
    response = SimpleNamespace(source_nodes=[node("Old Quarry Trail", "Hazards")])
    assert retrieved_sections(response) == ["Old Quarry Trail / Hazards"]


def test_traced_function_runs_with_tracking_disabled():
    # With OPIK_TRACK_DISABLE=true, @opik.track is a pass-through: the function
    # runs normally, nothing is sent, and flushing is a harmless no-op.
    import opik

    @opik.track(name="label_for_test")
    def label(trail: str, section: str) -> str:
        return suite.section_label(trail, section)

    assert label("A", "B") == "A / B"
    opik.flush_tracker()
