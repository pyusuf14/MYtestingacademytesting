"""Chunking: split Documents into Chunks with per-source size/overlap."""
from __future__ import annotations

import hashlib
import re

from .models import Chunk, Document

# Per-source chunking policy (char-based, with token-ish semantics).
# code/tickets/testcases are structured so they are usually kept whole unless
# they exceed the cap, at which point they are split with overlap.
SOURCE_POLICY = {
    "docs": {"size": 1200, "overlap": 150},
    "meeting": {"size": 1000, "overlap": 100},
    "logs": {"size": 2000, "overlap": 200},
    "diagram": {"size": 800, "overlap": 0},
    "code": {"size": 2000, "overlap": 200},
    "testcases": {"size": 1500, "overlap": 0},
    "jira_export": {"size": 2500, "overlap": 0},
    "jira_live": {"size": 2500, "overlap": 0},
}


def _doc_id(doc: Document) -> str:
    h = hashlib.sha1(f"{doc.source_type}:{doc.source_path}:{doc.title}".encode()).hexdigest()[:16]
    return h


def _split_with_overlap(text: str, size: int, overlap: int) -> list[str]:
    text = text.strip()
    if not text:
        return []
    if len(text) <= size:
        return [text]
    chunks: list[str] = []
    start = 0
    step = max(1, size - overlap)
    while start < len(text):
        end = min(start + size, len(text))
        piece = text[start:end].strip()
        if piece:
            chunks.append(piece)
        if end >= len(text):
            break
        start += step
    return chunks


def _split_sentences(text: str, size: int) -> list[str]:
    """Sentence-aware splitter for prose that tries to break on boundaries."""
    text = text.strip()
    if not text:
        return []
    if len(text) <= size:
        return [text]
    sentences = re.split(r"(?<=[.!?])\s+", text)
    chunks: list[str] = []
    buf = ""
    for sent in sentences:
        if len(buf) + len(sent) <= size:
            buf = (buf + " " + sent).strip()
        else:
            if buf:
                chunks.append(buf)
            buf = sent
            while len(buf) > size:
                chunks.append(buf[:size].strip())
                buf = buf[size:].strip()
    if buf:
        chunks.append(buf)
    return chunks


def chunk_document(doc: Document) -> list[Chunk]:
    policy = SOURCE_POLICY.get(doc.source_type, {"size": 1200, "overlap": 100})
    size = policy["size"]
    overlap = policy["overlap"]
    did = _doc_id(doc)

    if overlap > 0 and doc.source_type in ("docs", "meeting", "logs"):
        pieces = _split_sentences(doc.text, size)
    elif overlap > 0:
        pieces = _split_with_overlap(doc.text, size, overlap)
    else:
        pieces = _split_with_overlap(doc.text, size, 0)

    chunks: list[Chunk] = []
    for i, piece in enumerate(pieces):
        chunks.append(Chunk(
            doc_id=did,
            text=piece,
            source_type=doc.source_type,
            source_path=doc.source_path,
            title=doc.title,
            metadata=dict(doc.metadata),
            chunk_index=i,
        ))
    return chunks


def chunk_documents(docs: list[Document]) -> list[Chunk]:
    out: list[Chunk] = []
    for doc in docs:
        out.extend(chunk_document(doc))
    return out
