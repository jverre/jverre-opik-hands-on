"""Embedding index and similarity search over the guide chunks."""

import opik
from langchain_core.embeddings import Embeddings
from langchain_core.vectorstores import InMemoryVectorStore
from langchain_openai import OpenAIEmbeddings


def build_store(chunks: list[str], embeddings: Embeddings | None = None) -> InMemoryVectorStore:
    """Embed every chunk once, in memory (about twenty short passages)."""
    embeddings = embeddings or OpenAIEmbeddings(model="text-embedding-3-small")
    return InMemoryVectorStore.from_texts(chunks, embeddings)


# A named tool span for retrieval: input is the question and k, output is the k chunks,
# and it nests under the graph's "retrieve" node. ignore_arguments keeps the store's
# object repr out of the span input.
@opik.track(name="vector_search", type="tool", ignore_arguments=["store"])
def search(store: InMemoryVectorStore, question: str, k: int) -> list[str]:
    """Return the text of the k chunks most similar to the question."""
    return [doc.page_content for doc in store.similarity_search(question, k=k)]
