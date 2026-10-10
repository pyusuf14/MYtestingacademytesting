"""Core data structures for QABuddy.ai."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class Document:
    """A parsed source file (or row/ticket), before chunking."""

    source_type: str  # docs, testcases, jira_export, jira_live, code, logs, meeting, diagram
    source_path: str  # filesystem path or JIRA key
    title: str
    text: str
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class Chunk:
    """A chunked piece of text ready to embed."""

    doc_id: str
    text: str
    source_type: str
    source_path: str
    title: str
    metadata: dict[str, Any] = field(default_factory=dict)
    chunk_index: int = 0

    @property
    def citation(self) -> str:
        """Human-readable citation for this chunk."""
        src = self.metadata.get("citation", self.source_path)
        if self.metadata.get("ticket_key"):
            src = self.metadata["ticket_key"]
        return f"{src}"
