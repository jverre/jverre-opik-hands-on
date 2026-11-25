"""Run the redaction pipeline over the fictional documents in data/."""

import json
from pathlib import Path

from dotenv import find_dotenv, load_dotenv
from openai import OpenAI

from pipeline import process_document

load_dotenv(find_dotenv(usecwd=True))


def main() -> None:
    docs = json.loads((Path(__file__).parent / "data" / "documents.json").read_text())
    client = OpenAI()
    for doc in docs:
        result = process_document(client, doc)
        print(f"\n== {doc['id']}  entities={len(result['entities'])}  leak_free={result['leak_free']}"
              f"  recall={result['recall']}  precision={result['precision']}")
        print(result["redacted"])


if __name__ == "__main__":
    main()
