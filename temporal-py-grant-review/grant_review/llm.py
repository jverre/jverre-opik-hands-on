"""Small OpenAI helpers used by the two model-backed activities."""

import json

from openai import AsyncOpenAI

from .config import MODEL


async def chat_json(system: str, user: str) -> tuple[dict, object]:
    """One JSON-mode completion; returns (parsed JSON, raw response)."""
    client = AsyncOpenAI()
    response = await client.chat.completions.create(
        model=MODEL,
        temperature=0,
        response_format={"type": "json_object"},
        messages=[{"role": "system", "content": system}, {"role": "user", "content": user}],
    )
    return json.loads(response.choices[0].message.content or "{}"), response


async def chat_text(system: str, user: str) -> tuple[str, object]:
    client = AsyncOpenAI()
    response = await client.chat.completions.create(
        model=MODEL,
        temperature=0.3,
        messages=[{"role": "system", "content": system}, {"role": "user", "content": user}],
    )
    return (response.choices[0].message.content or "").strip(), response
