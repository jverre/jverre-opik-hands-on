import pathlib
from types import SimpleNamespace

import main

DATA = pathlib.Path(main.__file__).parent / "data"


def test_corpus_has_sections_from_every_file():
    sources = {e["source"] for e in main.load_corpus(DATA)}
    assert sources == {p.name for p in DATA.glob("*.md")}
    assert len(main.CORPUS) >= 15


def test_search_finds_the_trigger_evidence():
    # Runs the @opik.track-decorated tool with tracking disabled: it must behave as a plain function.
    hits = main.search_corpus("retry policy change in build 4127 report-exporter")
    assert len(hits) == 3
    assert any(h["source"] == "deploy-notes.md" for h in hits)


def test_search_ignores_stopwords():
    assert main.rarity("zzzz", main.CORPUS) == 0.0
    assert main.search_corpus("the and of") is not None


def test_route_loops_until_all_inquiries_answered():
    state = {"inquiries": ["a", "b"], "findings": [{}]}
    assert main.route_investigation(state) == "investigator"
    state["findings"].append({})
    assert main.route_investigation(state) == "writer"


def test_investigator_appends_finding_with_stubbed_llm(monkeypatch):
    class Stub:
        def invoke(self, messages):
            assert "Answer using only the evidence" in messages[0][1]
            return SimpleNamespace(content="stub answer")

    monkeypatch.setattr(main, "get_llm", lambda: Stub())
    out = main.investigator({"inquiries": ["When did the pager fire?"], "findings": []})
    assert out["findings"][0]["answer"] == "stub answer"
    assert out["findings"][0]["sources"]


def test_format_notes_lists_sources():
    text = main.format_notes([{"inquiry": "Q", "answer": "A", "sources": ["x.md", "y.md"]}])
    assert "### Q" in text and "x.md, y.md" in text


def test_graph_runs_end_to_end_with_stub(monkeypatch):
    class Stub:
        def with_structured_output(self, schema):
            return SimpleNamespace(invoke=lambda m: schema(inquiries=["q1", "q2"]))

        def invoke(self, messages):
            return SimpleNamespace(content="text")

    monkeypatch.setattr(main, "get_llm", lambda: Stub())
    result = main.build_graph().invoke({"incident": "x"})
    assert len(result["findings"]) == 2 and result["draft"] == "text"
