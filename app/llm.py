"""Isolated LLM access so agents don't care which provider is used."""
import json
import logging

from app.core.config import settings

logger = logging.getLogger(__name__)

_client = None
if settings.anthropic_api_key:
    import anthropic
    _client = anthropic.Anthropic(api_key=settings.anthropic_api_key)


def call_llm(system: str, prompt: str, max_tokens: int = 500) -> str:
    """Call Claude if configured, else raise so callers can fall back."""
    if not _client:
        raise RuntimeError("No LLM configured (set ANTHROPIC_API_KEY)")

    response = _client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=max_tokens,
        system=system,
        messages=[{"role": "user", "content": prompt}],
    )
    return "".join(block.text for block in response.content if block.type == "text")


def call_llm_json(system: str, prompt: str, max_tokens: int = 500) -> dict:
    """Call the LLM and parse a strict-JSON response."""
    raw = call_llm(system + "\n\nRespond ONLY with valid JSON. No preamble, no markdown fences.", prompt, max_tokens)
    cleaned = raw.strip().strip("`")
    if cleaned.startswith("json"):
        cleaned = cleaned[4:].strip()
    return json.loads(cleaned)


def llm_available() -> bool:
    return _client is not None
