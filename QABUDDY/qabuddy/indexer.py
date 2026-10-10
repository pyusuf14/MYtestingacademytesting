"""Qdrant indexing: create collection and upsert chunks (dense + sparse)."""
from __future__ import annotations

import uuid

from qdrant_client import QdrantClient
from qdrant_client.http import models as qm

from . import config
from .chunking import chunk_documents
from .embed import get_embedder
from .models import Chunk, Document

# Sparse vector for keyword (BM25-style) retrieval — generated locally from
# text tokens so we get hybrid search without an external sparse model.
def _sparse_from_text(text: str) -> tuple[list[int], list[float]]:
    tokens = {}
    for tok in text.lower().split():
        # crude token id via hash; collisions acceptable for BM25-style boost
        idx = abs(hash(tok)) % 1_000_000
        tokens[idx] = tokens.get(idx, 0.0) + 1.0
    if not tokens:
        return [], []
    indices = sorted(tokens)
    # normalize
    total = sum(tokens.values())
    values = [tokens[i] / total for i in indices]
    return indices, values


def _vector_dim() -> int:
    emb = get_embedder(config.EMBED_MODEL)
    v = emb.embed(["dimension probe"])
    return len(v[0])


def get_client() -> QdrantClient:
    return QdrantClient(path=config.QDRANT_PATH)


def ensure_collection(client: QdrantClient, dim: int) -> None:
    if client.collection_exists(config.COLLECTION_NAME):
        return
    client.create_collection(
        collection_name=config.COLLECTION_NAME,
        vectors_config={
            "dense": qm.VectorParams(size=dim, distance=qm.Distance.COSINE),
        },
        sparse_vectors_config={
            "sparse": qm.SparseVectorParams(),
        },
    )


def index_documents(documents: list[Document]) -> int:
    chunks: list[Chunk] = chunk_documents(documents)
    if not chunks:
        return 0

    emb = get_embedder(config.EMBED_MODEL)
    texts = [c.text for c in chunks]
    dense = emb.embed(texts)

    client = get_client()
    dim = len(dense[0])
    ensure_collection(client, dim)

    points = []
    for i, c in enumerate(chunks):
        si, sv = _sparse_from_text(c.text)
        payload = {
            "text": c.text,
            "source_type": c.source_type,
            "source_path": c.source_path,
            "title": c.title,
            "chunk_index": c.chunk_index,
            "doc_id": c.doc_id,
            **{k: v for k, v in c.metadata.items() if isinstance(v, (str, int, float, bool))},
        }
        points.append(qm.PointStruct(
            id=str(uuid.uuid4()),
            vector={
                "dense": dense[i],
                "sparse": qm.SparseVector(indices=si, values=sv),
            },
            payload=payload,
        ))

    client.upsert(collection_name=config.COLLECTION_NAME, points=points)
    return len(chunks)
