import os
from openai import OpenAI

_client = None
MODEL = "gpt-4o-mini"


def _get_client() -> OpenAI:
    global _client
    if _client is None:
        _client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    return _client


def call_llm(messages: list[dict]) -> str:
    """Send messages to GPT-4o-mini and return the answer."""
    response = _get_client().chat.completions.create(
        model=MODEL,
        messages=messages,
        temperature=0.2,
    )
    return response.choices[0].message.content
