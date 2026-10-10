"""QABuddy.ai pipeline CLI.

Usage:
    python -m qabuddy.pipeline ingest   # parse + chunk + embed + index
    python -m qabuddy.pipeline ask "..." # one-shot retrieval + answer
    python -m qabuddy.pipeline serve     # start FastAPI chatbot
"""
from __future__ import annotations

import sys
from pathlib import Path

from . import config
from .ingest import parse_file
from .jira import fetch_tickets, is_configured
from .models import Document
from .indexer import index_documents


def collect_local_documents() -> list[Document]:
    root = Path(config.DATA_DIR)
    docs: list[Document] = []
    for folder, source_type in config.SOURCE_FOLDERS.items():
        folder_path = root / folder
        if not folder_path.exists():
            print(f"  [skip] folder not found: {folder}")
            continue
        files = sorted(p for p in folder_path.rglob("*") if p.is_file())
        if not files:
            print(f"  [skip] empty folder: {folder}")
            continue
        for f in files:
            parsed = parse_file(f, source_type)
            docs.extend(parsed)
            if parsed:
                print(f"  [parse] {f.relative_to(root)} -> {len(parsed)} doc(s)")
    return docs


def run_ingest() -> int:
    print("== QABuddy.ai ingestion ==")
    docs = collect_local_documents()
    print(f"  collected {len(docs)} local documents")

    if is_configured():
        try:
            jira_docs = fetch_tickets()
            print(f"  [jira] fetched {len(jira_docs)} tickets")
            docs.extend(jira_docs)
        except Exception as ex:
            print(f"  [jira] ERROR: {ex}")
    else:
        print("  [jira] not configured — skipping live tickets")

    if not docs:
        print("No documents to index.")
        return 1

    n = index_documents(docs)
    print(f"  indexed {n} chunks into Qdrant ({config.COLLECTION_NAME})")
    return 0


def run_ask(query: str, top_k: int = 8) -> int:
    from .retrieve import retrieve
    from .synthesize import synthesize

    chunks = retrieve(query, top_k=top_k)
    result = synthesize(query, chunks)
    print(result["answer"])
    if result["citations"]:
        print("\n--- Citations ---")
        for c in result["citations"]:
            print(f"  * {c}")
    return 0


def run_build_graph() -> int:
    print("== QABuddy.ai graph build ==")
    docs = collect_local_documents()
    if not docs:
        print("No documents to build a graph from.")
        return 1
    from .chunking import chunk_documents
    from .graph import build_graph, save_graph

    chunks = chunk_documents(docs)
    print(f"  collected {len(docs)} documents -> {len(chunks)} chunks")
    G = build_graph(chunks)
    save_graph(G, config.GRAPH_PATH)
    print(
        f"  saved graph: {G.number_of_nodes()} entities, "
        f"{G.number_of_edges()} relations -> {config.GRAPH_PATH}"
    )
    return 0


def main() -> int:
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass
    args = sys.argv[1:]
    if not args:
        print(__doc__)
        return 1
    cmd = args[0]
    if cmd == "ingest":
        return run_ingest()
    if cmd == "ask":
        q = " ".join(args[1:]) or "How does the login flow work?"
        return run_ask(q)
    if cmd == "build-graph":
        return run_build_graph()
    if cmd == "serve":
        import uvicorn

        uvicorn.run("qabuddy.chat:app", host="0.0.0.0", port=8000, reload=False)
        return 0
    print(__doc__)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
