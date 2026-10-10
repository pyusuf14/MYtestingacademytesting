"""QABuddy.ai — configuration loaded from environment / .env."""
from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv

APP_DIR = Path(__file__).resolve().parent
load_dotenv(APP_DIR / ".env")


def _path(value: str) -> str:
    """Resolve a possibly-relative path against the app directory."""
    p = Path(value)
    if not p.is_absolute():
        p = (APP_DIR / value).resolve()
    return str(p)


# JIRA
JIRA_BASE_URL = os.getenv("JIRA_BASE_URL", "").rstrip("/")
JIRA_EMAIL = os.getenv("JIRA_EMAIL", "")
JIRA_PAT = os.getenv("JIRA_PAT", "")
JIRA_JQL = os.getenv("JIRA_JQL", "project IN (KAN, SAM1) ORDER BY created DESC")

# Embeddings
EMBED_MODEL = os.getenv("EMBED_MODEL", "BAAI/bge-small-en-v1.5")

# Vector store
QDRANT_PATH = _path(os.getenv("QDRANT_PATH", "./.qabuddy/qdrant"))
COLLECTION_NAME = os.getenv("COLLECTION_NAME", "qabuddy_kb")

# Data sources: root containing the 9 source folders (defaults to QABUDDY root)
DATA_DIR = _path(os.getenv("DATA_DIR", "../"))

# Optional LLM
LLM_API_BASE = os.getenv("LLM_API_BASE", "")
LLM_API_KEY = os.getenv("LLM_API_KEY", "")
LLM_MODEL = os.getenv("LLM_MODEL", "")

# CORS: allowed origins for the web UI (comma-separated). "*" allows any.
CORS_ORIGINS = os.getenv("CORS_ORIGINS", "*")

# Re-ranker (cross-encoder)
RERANK_ENABLED = os.getenv("RERANK_ENABLED", "1") == "1"
RERANK_MODEL = os.getenv("RERANK_MODEL", "cross-encoder/ms-marco-MiniLM-L-6-v2")
RERANK_POOL = int(os.getenv("RERANK_POOL", "24"))

# Graph RAG
GRAPH_ENABLED = os.getenv("GRAPH_ENABLED", "1") == "1"
GRAPH_PATH = _path(os.getenv("GRAPH_PATH", "./.qabuddy/graph.json"))
GRAPH_TOP_K = int(os.getenv("GRAPH_TOP_K", "4"))
# Source types to exclude from the knowledge graph (formulaic/high-volume).
GRAPH_SKIP_TYPES = {
    t.strip() for t in os.getenv("GRAPH_SKIP_TYPES", "testcases,code").split(",") if t.strip()
}
# Use the LLM for entity extraction (rate-limit heavy); defaults to fast
# deterministic extraction (ticket IDs + key phrases) which needs no LLM.
GRAPH_USE_LLM = os.getenv("GRAPH_USE_LLM", "0") == "1"

# Which source folders to ingest (keys are folder names, values are source types)
SOURCE_FOLDERS = {
    "Company Docs": "docs",
    "JIRA tickets": "jira_export",
    "Lucid charts": "diagram",
    "PRD": "docs",
    "Testcases": "testcases",
    "jenkins log": "logs",
    "meeting notes": "meeting",
    "sourcecodes": "code",
    # figma designs is Phase 2, excluded from ingestion.
}
