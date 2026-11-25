"""Offline tests: fake embeddings and a stub chat model, no keys, no Opik."""

import pytest
from langchain_core.embeddings import DeterministicFakeEmbedding
from langchain_core.language_models.fake_chat_models import FakeListChatModel

from guide.corpus import load_chunks
from guide.evaluation import DATASET_ITEMS, make_task
from guide.graph import SYSTEM_PROMPT, build_graph, format_context
from guide.retrieval import build_store, search


@pytest.fixture(scope="module")
def store():
    return build_store(load_chunks(), DeterministicFakeEmbedding(size=64))


def test_chunks_are_one_per_section_and_carry_their_title():
    chunks = load_chunks()
    assert len(chunks) == 20
    assert all(" / " in c.splitlines()[0] for c in chunks)
    assert any(c.startswith("Accessibility at the Alderbank Museum / Step-free access") for c in chunks)


def test_search_returns_exactly_k_chunks(store):
    # search() is an @opik.track tool span; with tracking disabled it is a plain call.
    assert len(search(store, "opening hours", k=4)) == 4
    assert len(search(store, "opening hours", k=1)) == 1


def test_format_context_separates_chunks():
    assert format_context(["a", "b"]) == "a\n\n---\n\nb"
    assert "a\n\n---\n\nb" in SYSTEM_PROMPT.format(context=format_context(["a", "b"]))


def test_graph_retrieves_k_chunks_then_answers_from_them(store):
    llm = FakeListChatModel(responses=["Closes at 17:00."])
    app = build_graph(store, llm, k=2)
    result = app.invoke({"question": "When does the Orrery Room close?"})
    assert result["answer"] == "Closes at 17:00."
    assert len(result["context"]) == 2


def test_task_returns_output_and_context_for_the_judges(store):
    app = build_graph(store, FakeListChatModel(responses=["ok"]), k=3)
    out = make_task(app)({"question": "Is there a cafe?"})
    assert out["output"] == "ok"
    assert len(out["context"]) == 3


def test_dataset_items_are_well_formed():
    assert len(DATASET_ITEMS) >= 8
    assert all(i["question"] and i["expected_output"] for i in DATASET_ITEMS)
