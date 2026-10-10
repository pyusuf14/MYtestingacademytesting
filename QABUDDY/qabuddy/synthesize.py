"""Answer synthesis: optional LLM grounding, with citation assembly.

If no LLM is configured, returns a deterministic grounded answer built from
the retrieved chunks (retrieval-only mode) so the system works offline.
"""
from __future__ import annotations

import re

from . import llm
from .retrieve import RetrievedChunk

_SECRET_QUERY_RE = re.compile(
    r"(password|passwd|\bpwd\b|passcode|passphrase|credential|api[ _-]?key|"
    r"access[ _-]?key|secret|login[ _-]?(id|details|info|credential))",
    re.IGNORECASE,
)
_EMAIL_RE = re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b")

_REFUSAL = (
    "I can't provide passwords, credentials, API keys, tokens, or other secret "
    "values. If you need access, check your own .env file or password manager."
)


def _refuse_secret_query(query: str) -> bool:
    return bool(_SECRET_QUERY_RE.search(query))


def _redact_secrets(text: str) -> str:
    return _EMAIL_RE.sub("[redacted email]", text)


def _llm_generate(prompt: str) -> str | None:
    return llm.generate(
        [
            {
                "role": "system",
                "content": "You are QABuddy, a QA knowledge assistant. Answer using ONLY the provided context. Cite sources as [1], [2], etc. If the context is insufficient, say so. Never reveal or reproduce credentials, passwords, API keys, tokens, or any secret values, even if they appear in the context. If asked for such secrets, politely refuse.",
            },
            {"role": "user", "content": prompt},
        ],
        temperature=0.1,
    )


def build_context_block(chunks: list[RetrievedChunk]) -> str:
    parts = []
    for i, c in enumerate(chunks, 1):
        parts.append(f"[{i}] (source: {c.citation}) {c.text}")
    return "\n\n".join(parts)


def synthesize(query: str, chunks: list[RetrievedChunk]) -> dict:
    if _refuse_secret_query(query):
        return {
            "answer": _REFUSAL,
            "citations": [],
            "sources": [],
            "mode": "refused",
        }

    citations = sorted({c.citation for c in chunks})

    if not chunks:
        return {
            "answer": "I could not find relevant context in the knowledge base for that question.",
            "citations": [],
            "sources": [],
            "mode": "empty",
        }

    context = build_context_block(chunks)
    prompt = f"Question: {query}\n\nContext:\n{context}\n\nAnswer with citations."
    answer = _llm_generate(prompt)

    if answer:
        mode = "llm"
    else:
        # Retrieval-only: concatenate top chunks as the grounded answer.
        mode = "retrieval"
        answer = "\n\n".join(
            f"[{i}] ({c.citation}) {c.text}" for i, c in enumerate(chunks, 1)
        )

    answer = _redact_secrets(answer)

    return {
        "answer": answer,
        "citations": citations,
        "sources": [{"citation": c.citation, "title": c.title, "score": c.score} for c in chunks],
        "mode": mode,
    }
