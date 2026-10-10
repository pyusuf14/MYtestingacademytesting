"""Graph RAG: a lightweight knowledge graph built from the corpus.

Build phase extracts entities + relations per document using the configured
LLM, stores them as a NetworkX graph (entities = nodes, relations = edges),
and persists to JSON. Query phase extracts entities from the question, matches
them in the graph, and returns related chunks (matched nodes + 1-hop
neighbours) to augment retrieval.
"""
from __future__ import annotations

import json
import re
import time
from pathlib import Path

import networkx as nx

from . import config
from .llm import generate

_EXTRACT_PROMPT = """Extract the key entities and relationships from the text below for a QA knowledge graph.
Entities are concrete things: systems, features, modules, pages, test areas, tools, roles, or ticket IDs.
Return ONLY a JSON object with this exact shape:
{"entities": ["...", "..."], "relations": [{"subject": "...", "relation": "...", "object": "..."}]}

Text:
{text}
"""

_QUERY_PROMPT = """Extract the key entities (systems, features, modules, pages, tools, roles, ticket IDs)
from this question. Return ONLY a JSON array of strings.

Question: {query}
"""


def _extract_json(text: str) -> dict:
    if not text:
        return {"entities": [], "relations": []}
    # Strip markdown code fences if present, then isolate the JSON object/array.
    text = re.sub(r"```(?:json)?", "", text).strip()
    m = re.search(r"\{.*\}", text, re.S)
    if m:
        text = m.group(0)
    try:
        data = json.loads(text)
    except json.JSONDecodeError:
        return {"entities": [], "relations": []}
    return {
        "entities": [str(e).strip() for e in data.get("entities", []) if str(e).strip()],
        "relations": [r for r in data.get("relations", []) if isinstance(r, dict)],
    }


_STOP = {
    "the", "a", "an", "and", "or", "of", "to", "in", "for", "on", "with", "is",
    "are", "be", "as", "at", "by", "this", "that", "these", "those", "it", "its",
    "from", "via", "using", "into", "not", "also", "can", "will", "should",
}


def _extract_document_fast(text: str) -> dict:
    """Deterministic extraction: ticket IDs + title-case key phrases, co-occurrence edges."""
    tickets = re.findall(r"\b[A-Z][A-Z0-9]{1,}-\d+\b", text)
    phrases = re.findall(r"\b(?:[A-Z][a-zA-Z0-9]*\s+){1,3}[A-Z][a-zA-Z0-9]*\b", text)

    entities: list[str] = []
    seen: set[str] = set()
    for t in tickets:
        key = t.lower()
        if key not in seen:
            seen.add(key)
            entities.append(t)
    for p in phrases:
        words = p.split()
        if len(words) < 2:
            continue
        if all(w.lower() not in _STOP for w in words):
            key = p.lower()
            if key not in seen:
                seen.add(key)
                entities.append(p)
        if len(entities) >= 25:
            break

    relations = [
        {"subject": entities[i], "relation": "co-occurs_with", "object": entities[i + 1]}
        for i in range(len(entities) - 1)
    ]
    return {"entities": entities, "relations": relations}


def _extract_document(text: str) -> dict:
    if not config.GRAPH_USE_LLM:
        return _extract_document_fast(text)
    try:
        out = generate(
            [{"role": "user", "content": _EXTRACT_PROMPT.replace("{text}", text[:1500])}],
            temperature=0,
        )
    except Exception:
        return _extract_document_fast(text)
    data = _extract_json(out or "")
    if not data["entities"]:
        return _extract_document_fast(text)
    return data


def _query_entities(query: str) -> list[str]:
    try:
        out = generate(
            [{"role": "user", "content": _QUERY_PROMPT.replace("{query}", query)}],
            temperature=0,
        )
    except Exception:
        return []
    if not out:
        return []
    text = re.sub(r"```(?:json)?", "", out).strip()
    m = re.search(r"\[.*\]", text, re.S)
    if m:
        text = m.group(0)
    try:
        data = json.loads(text)
    except json.JSONDecodeError:
        return []
    if isinstance(data, list):
        return [str(e).strip().lower() for e in data if str(e).strip()]
    return []


def _chunk_ref(chunk) -> dict:
    return {
        "doc_id": chunk.doc_id,
        "chunk_index": chunk.chunk_index,
        "text": chunk.text,
        "citation": chunk.metadata.get("citation", chunk.source_path),
        "title": chunk.title,
        "source_type": chunk.source_type,
        "source_path": chunk.source_path,
    }


def build_graph(chunks: list) -> nx.DiGraph:
    """Group chunks by document, extract entities per document, build the graph."""
    by_doc: dict[str, list] = {}
    for c in chunks:
        if c.source_type in config.GRAPH_SKIP_TYPES:
            continue
        by_doc.setdefault(c.doc_id, []).append(c)

    G = nx.DiGraph()
    for i, (doc_id, doc_chunks) in enumerate(by_doc.items(), 1):
        text = "\n".join(c.text for c in doc_chunks[:6])
        data = _extract_document(text)
        refs = [_chunk_ref(c) for c in doc_chunks]
        if config.GRAPH_USE_LLM:
            time.sleep(2.5)  # pace LLM requests to stay under token rate limits

        for ent in data["entities"]:
            ent = ent.lower()
            if ent not in G:
                G.add_node(ent, chunks=[])
            existing = {r["doc_id"] + ":" + str(r["chunk_index"]) for r in G.nodes[ent]["chunks"]}
            for r in refs:
                key = r["doc_id"] + ":" + str(r["chunk_index"])
                if key not in existing:
                    G.nodes[ent]["chunks"].append(r)
                    existing.add(key)

        for rel in data["relations"]:
            s = str(rel.get("subject", "")).strip().lower()
            o = str(rel.get("object", "")).strip().lower()
            if s and o:
                G.add_edge(s, o, relation=str(rel.get("relation", "related")))

        if i % 5 == 0:
            print(f"  [graph] built {i}/{len(by_doc)} documents ({G.number_of_nodes()} entities)", flush=True)

    return G


def save_graph(G: nx.DiGraph, path: Path | str) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(nx.node_link_data(G, edges="links")), encoding="utf-8")


def load_graph(path: Path | str) -> nx.DiGraph | None:
    path = Path(path)
    if not path.exists():
        return None
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        return nx.node_link_graph(data, edges="links")
    except (json.JSONDecodeError, KeyError):
        return None


def _match(node: str, query_entity: str) -> bool:
    return node == query_entity or query_entity in node or node in query_entity


def graph_search(query: str, G: nx.DiGraph, top_k: int) -> list[dict]:
    """Return related chunk refs for a query, from matched entities + neighbours."""
    if G is None or G.number_of_nodes() == 0:
        return []

    q_entities = _query_entities(query)
    matched_nodes: set[str] = set()
    for qe in q_entities:
        for node in G.nodes:
            if _match(str(node), qe):
                matched_nodes.add(node)

    results: dict[str, dict] = {}

    def collect(node: str) -> None:
        for r in G.nodes[node].get("chunks", []):
            key = r["doc_id"] + ":" + str(r["chunk_index"])
            if key not in results:
                results[key] = r

    for node in matched_nodes:
        collect(node)
        for _, nbr in G.edges(node):
            collect(nbr)
        for nbr, _ in G.in_edges(node):
            collect(nbr)

    return list(results.values())[:top_k]
