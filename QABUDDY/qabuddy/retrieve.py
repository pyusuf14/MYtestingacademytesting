"""Hybrid retrieval: dense (BGE) + sparse (keyword) + graph, then re-ranked.

Pipeline:
1. Dense search (BGE) and sparse search (BM25-style keyword).
2. Reciprocal-rank fusion of the two ranked lists.
3. Graph RAG: add chunks linked to entities in the question.
4. Cross-encoder re-ranking of the combined candidate pool.
5. Return the top-k chunks with source citations.
"""
from __future__ import annotations

from dataclasses import dataclass

from qdrant_client import QdrantClient
from qdrant_client.http import models as qm

from . import config
from .embed import get_embedder
from .indexer import _sparse_from_text
from .rerank import rerank


@dataclass
class RetrievedChunk:
    score: float
    text: str
    source_type: str
    source_path: str
    title: str
    citation: str
    metadata: dict


def _client() -> QdrantClient:
    from qdrant_client import QdrantClient

    return QdrantClient(path=config.QDRANT_PATH)


def _dense_search(client: QdrantClient, query_vec: list[float], k: int) -> list[tuple[str, float]]:
    res = client.query_points(
        collection_name=config.COLLECTION_NAME,
        query=query_vec,
        using="dense",
        limit=k,
        with_payload=True,
    )
    return [(p.id, p.score) for p in res.points]


def _sparse_search(client: QdrantClient, query_text: str, k: int) -> list[tuple[str, float]]:
    si, sv = _sparse_from_text(query_text)
    if not si:
        return []
    sparse = qm.SparseVector(indices=si, values=sv)
    res = client.query_points(
        collection_name=config.COLLECTION_NAME,
        query=sparse,
        using="sparse",
        limit=k,
        with_payload=True,
    )
    return [(p.id, p.score) for p in res.points]


def _reciprocal_rank_fusion(ranked_lists: list[list[str]], k: int = 60) -> list[tuple[str, float]]:
    scores: dict[str, float] = {}
    for ranked in ranked_lists:
        for rank, pid in enumerate(ranked):
            scores[pid] = scores.get(pid, 0.0) + 1.0 / (k + rank + 1)
    return sorted(scores.items(), key=lambda x: x[1], reverse=True)


def _fetch_payloads(client: QdrantClient, ids: list[str]) -> dict[str, dict]:
    if not ids:
        return {}
    res = client.retrieve(
        collection_name=config.COLLECTION_NAME,
        ids=ids,
        with_payload=True,
    )
    return {p.id: p.payload for p in res}


def _candidate_from_payload(p: dict, score: float) -> dict:
    citation = p.get("ticket_key") or p.get("citation") or p.get("source_path", "")
    return {
        "text": p.get("text", ""),
        "citation": str(citation),
        "source_type": p.get("source_type", ""),
        "source_path": p.get("source_path", ""),
        "title": p.get("title", ""),
        "metadata": {k: v for k, v in p.items() if k != "text"},
        "score": score,
        "key": (p.get("doc_id"), p.get("chunk_index")),
    }


def retrieve(query: str, top_k: int = 8) -> list[RetrievedChunk]:
    client = _client()
    if not client.collection_exists(config.COLLECTION_NAME):
        return []

    emb = get_embedder(config.EMBED_MODEL)
    query_vec = emb.embed([query])[0]

    dense = _dense_search(client, query_vec, k=top_k * 3)
    sparse = _sparse_search(client, query_text=query, k=top_k * 3)

    fused = _reciprocal_rank_fusion(
        [[pid for pid, _ in dense], [pid for pid, _ in sparse]], k=60
    )
    fused_by_id = dict(fused)

    pool_ids = [pid for pid, _ in fused[: config.RERANK_POOL]]
    payloads = _fetch_payloads(client, pool_ids)

    candidates: list[dict] = []
    seen: set = set()
    for pid in pool_ids:
        p = payloads.get(pid)
        if not p:
            continue
        cand = _candidate_from_payload(p, fused_by_id.get(pid, 0.0))
        if cand["key"] in seen:
            continue
        candidates.append(cand)
        seen.add(cand["key"])

    # Graph RAG: augment with chunks linked to the question's entities.
    if config.GRAPH_ENABLED:
        from .graph import graph_search, load_graph

        G = load_graph(config.GRAPH_PATH)
        if G is not None:
            for gr in graph_search(query, G, config.GRAPH_TOP_K):
                key = (gr.get("doc_id"), gr.get("chunk_index"))
                if key in seen:
                    continue
                candidates.append(
                    {
                        "text": gr.get("text", ""),
                        "citation": str(gr.get("citation", "")),
                        "source_type": gr.get("source_type", ""),
                        "source_path": gr.get("source_path", ""),
                        "title": gr.get("title", ""),
                        "metadata": {
                            "citation": gr.get("citation", ""),
                            "doc_id": gr.get("doc_id"),
                            "chunk_index": gr.get("chunk_index"),
                        },
                        "score": 0.0,
                        "key": key,
                    }
                )
                seen.add(key)

    # Cross-encoder re-ranking of the combined pool.
    if config.RERANK_ENABLED and candidates:
        scores = rerank(query, [c["text"] for c in candidates])
        for c, s in zip(candidates, scores):
            c["score"] = s
    candidates.sort(key=lambda c: c["score"], reverse=True)

    results: list[RetrievedChunk] = []
    for c in candidates[:top_k]:
        results.append(
            RetrievedChunk(
                score=round(c["score"], 5),
                text=c["text"],
                source_type=c["source_type"],
                source_path=c["source_path"],
                title=c["title"],
                citation=c["citation"],
                metadata=c["metadata"],
            )
        )
    return results
