"""Cross-encoder re-ranking of the fused candidate pool.

Loads a sentence-transformers CrossEncoder once and lazily. The model is only
loaded when RERANK_ENABLED is true and reranking is actually requested.
"""
from __future__ import annotations

from . import config

_reranker = None


def _load():
    global _reranker
    if _reranker is None:
        from sentence_transformers import CrossEncoder

        _reranker = CrossEncoder(config.RERANK_MODEL)
    return _reranker


def rerank(query: str, texts: list[str]) -> list[float]:
    """Return a relevance score in [0,1] for each (query, text) pair.

    When re-ranking is disabled, returns zeros so callers can fall back to
    their existing scores unchanged.
    """
    if not config.RERANK_ENABLED or not texts:
        return [0.0] * len(texts)
    model = _load()
    scores = model.predict([[query, t] for t in texts])
    return [float(s) for s in scores]
