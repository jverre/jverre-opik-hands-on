"""Run the redaction pipeline over the fictional documents in data/."""

import json
import os
from pathlib import Path

import opik
from dotenv import find_dotenv, load_dotenv
from openai import OpenAI

from pipeline import process_document

load_dotenv(find_dotenv(usecwd=True))


def main() -> None:
    docs = json.loads((Path(__file__).parent / "data" / "documents.json").read_text())
    client = OpenAI()
    # The low-level client: no decorators, no wrappers. Every trace and span below is an
    # explicit call. The project name decides which Opik project the traces land in.
    opik_client = opik.Opik(project_name=os.getenv("OPIK_PROJECT_NAME", "opik-py-redaction-pipeline"))
    for doc in docs:
        result = process_document(client, opik_client, doc)
        print(f"\n== {doc['id']}  entities={len(result['entities'])}  leak_free={result['leak_free']}"
              f"  recall={result['recall']}  precision={result['precision']}")
        print(result["redacted"])
    # flush() blocks until the background batch is uploaded; without it a short-lived
    # script exits first and the traces never arrive.
    opik_client.flush()


if __name__ == "__main__":
    main()
