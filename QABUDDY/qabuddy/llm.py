"""Shared OpenAI-compatible LLM helper (used for synthesis and graph extraction)."""
from __future__ import annotations

import time

from . import config


def generate(messages: list[dict], temperature: float = 0.1, timeout: int = 120, max_retries: int = 6) -> str | None:
    """Call the configured LLM with retry/backoff on rate limits.

    Returns the assistant text, or None if unconfigured or persistently failing.
    """
    if not (config.LLM_API_BASE and config.LLM_API_KEY and config.LLM_MODEL):
        return None
    import httpx

    url = config.LLM_API_BASE.rstrip("/") + "/chat/completions"
    for attempt in range(max_retries):
        resp = httpx.post(
            url,
            headers={"Authorization": f"Bearer {config.LLM_API_KEY}"},
            json={
                "model": config.LLM_MODEL,
                "messages": messages,
                "temperature": temperature,
            },
            timeout=timeout,
        )
        if resp.status_code == 429 or resp.status_code >= 500:
            if attempt < max_retries - 1:
                time.sleep(2 ** attempt)
                continue
            return None
        resp.raise_for_status()
        data = resp.json()
        return data["choices"][0]["message"]["content"]
    return None
