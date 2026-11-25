"""Offline tests: no Ollama, no Opik server, no keys."""

from langchain_core.documents import Document
from langchain_core.language_models.fake_chat_models import FakeListChatModel
from langchain_core.runnables import RunnableLambda

import rag
from checks import CASES, answer_has_fact


def test_load_chunks_splits_by_section_and_keeps_source():
    chunks = rag.load_chunks()
    assert len(chunks) == 16
    by_source = {c.metadata["source"] for c in chunks}
    assert by_source == {
        "mashing.md", "hops.md", "fermentation-troubleshooting.md", "sanitation.md",
    }
    assert any(c.metadata["section"] == "Sanitizer contact time" for c in chunks)


def test_every_case_points_at_a_chunk_that_holds_its_fact():
    chunks = rag.load_chunks()
    for case in CASES:
        holders = [
            c for c in chunks
            if c.metadata["source"] == case.expected_source
            and case.expected_fact.lower() in c.page_content.lower()
        ]
        assert holders, case.question


def test_format_context_separates_chunks():
    docs = [Document(page_content="a"), Document(page_content="b")]
    assert rag.format_context(docs) == "a\n\n---\n\nb"


def test_answer_has_fact_is_case_insensitive():
    assert answer_has_fact("Mash at 63 C.", "63") == 1.0
    assert answer_has_fact("Wait 2 MINUTES.", "2 minutes") == 1.0
    assert answer_has_fact("Mash hot.", "63") == 0.0


def test_chain_runs_with_stubbed_retriever_and_llm():
    doc = Document(
        page_content="Mash at 63 C.", metadata={"source": "mashing.md", "section": "Mash"}
    )
    retriever = RunnableLambda(lambda q: [doc])
    llm = FakeListChatModel(responses=["Mash at 63 C."])
    chain = rag.build_chain(retriever, llm=llm)
    assert chain.invoke("What mash temperature?") == "Mash at 63 C."


def test_search_handbook_runs_untouched_with_tracking_disabled():
    # make_search returns an @opik.track function; with tracking disabled it
    # behaves like the plain function it wraps.
    doc = Document(
        page_content="Mash at 63 C.",
        metadata={"source": "mashing.md", "section": "Mash temperature and body"},
    )
    search = rag.make_search(RunnableLambda(lambda q: [doc]))
    result = search("What mash temperature?")
    assert result["sections"] == ["mashing.md / Mash temperature and body"]
    assert "63 C" in result["context"]
