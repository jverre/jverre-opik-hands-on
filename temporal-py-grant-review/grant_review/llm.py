"""Small OpenAI helpers used by the two model-backed activities."""

import json

from openai import AsyncOpenAI

from .config import MODEL
from .tracing import llm_span, record_completion


async def chat_json(name: str, system: str, user: str) -> tuple[dict, object]:
    """One JSON-mode completion; returns (parsed JSON, raw response)."""
    client = AsyncOpenAI()
    # llm_span adds an `llm` span (model, tokens, cost) under the current RunActivity span.
    with llm_span(name, system, user) as span:
        response = await client.chat.completions.create(
            model=MODEL,
            temperature=0,
            response_format={"type": "json_object"},
            messages=[{"role": "system", "content": system}, {"role": "user", "content": user}],
        )
        content = response.choices[0].message.content or "{}"
        record_completion(span, response, content)
    return json.loads(content), response


async def chat_text(name: str, system: str, user: str) -> tuple[str, object]:
    client = AsyncOpenAI()
    # llm_span adds an `llm` span (model, tokens, cost) under the current RunActivity span.
    with llm_span(name, system, user) as span:
        response = await client.chat.completions.create(
            model=MODEL,
            temperature=0.3,
            messages=[{"role": "system", "content": system}, {"role": "user", "content": user}],
        )
        text = (response.choices[0].message.content or "").strip()
        record_completion(span, response, text)
    return text, response
