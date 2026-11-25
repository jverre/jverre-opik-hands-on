"""Ask the Copperkettle homebrewing handbook four questions, fully offline."""

import pathlib

import dotenv

# Optional: pick up OPIK_* and OLLAMA_URL from the repo-root .env.
dotenv.load_dotenv(pathlib.Path(__file__).parents[1] / ".env")

import rag  # noqa: E402

QUESTIONS = [
    "What temperature should I mash at for a dry, crisp saison?",
    "How should I add hops for a hazy IPA whirlpool?",
    "My fermentation is stuck at 1.030. What should I do first?",
    "How long does the sanitizer need to touch a surface?",
]


def main() -> None:
    chain = rag.build_chain(rag.build_retriever())
    for question in QUESTIONS:
        print(f"Q: {question}\nA: {chain.invoke(question)}\n")


if __name__ == "__main__":
    main()
