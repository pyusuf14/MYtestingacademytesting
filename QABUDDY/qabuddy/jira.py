"""JIRA Cloud ingestion via PAT (Basic auth against REST API v3).

Uses the new /rest/api/3/search/jql POST endpoint (the old /search GET was
removed). Falls back gracefully if JIRA is unreachable or unconfigured.
"""
from __future__ import annotations

import base64
import json
import urllib.error
import urllib.parse
import urllib.request

from . import config
from .models import Document

_SEARCH_FIELDS = [
    "summary", "description", "comment", "issuetype", "status",
    "priority", "labels", "components", "created", "updated",
    "reporter", "assignee", "fixVersions", "versions",
]


def _auth_header() -> str:
    creds = f"{config.JIRA_EMAIL}:{config.JIRA_PAT}".encode()
    return "Basic " + base64.b64encode(creds).decode()


def _jira_request(path: str, payload: dict | None = None):
    url = config.JIRA_BASE_URL + path
    headers = {"Authorization": _auth_header(), "Accept": "application/json"}
    data = None
    if payload is not None:
        headers["Content-Type"] = "application/json"
        data = json.dumps(payload).encode()
    req = urllib.request.Request(url, data=data, headers=headers, method="POST" if payload else "GET")
    with urllib.request.urlopen(req) as r:
        return json.load(r)


def is_configured() -> bool:
    return bool(config.JIRA_BASE_URL and config.JIRA_EMAIL and config.JIRA_PAT)


def _format_issue(issue: dict) -> Document:
    key = issue.get("key", "")
    fields = issue.get("fields", {})
    summary = fields.get("summary") or ""
    itype = (fields.get("issuetype") or {}).get("name", "")
    status = (fields.get("status") or {}).get("name", "")
    priority = (fields.get("priority") or {}).get("name", "")
    labels = ", ".join(fields.get("labels") or [])
    components = ", ".join((c.get("name", "") for c in (fields.get("components") or [])))
    created = fields.get("created", "")
    updated = fields.get("updated", "")
    reporter = (fields.get("reporter") or {}).get("displayName", "")
    assignee = (fields.get("assignee") or {}).get("displayName", "")

    desc = fields.get("description") or ""
    comments = fields.get("comment") or {}
    comment_blocks = []
    for cm in comments.get("comments", []):
        author = (cm.get("author") or {}).get("displayName", "")
        body = cm.get("body", "")
        comment_blocks.append(f"{author}: {body}")

    text = "\n".join(
        f"{k}: {v}" for k, v in [
            ("Key", key),
            ("Summary", summary),
            ("Type", itype),
            ("Status", status),
            ("Priority", priority),
            ("Labels", labels),
            ("Components", components),
            ("Created", created),
            ("Updated", updated),
            ("Reporter", reporter),
            ("Assignee", assignee),
            ("Description", desc),
        ] if v
    )
    if comment_blocks:
        text += "\nComments:\n" + "\n".join(comment_blocks)

    return Document(
        source_type="jira_live",
        source_path=f"jira:{key}",
        title=f"{key} — {summary}",
        text=text,
        metadata={
            "ticket_key": key,
            "ticket_type": itype,
            "status": status,
            "priority": priority,
            "labels": labels,
            "components": components,
            "citation": key,
        },
    )


def fetch_tickets(jql: str | None = None) -> list[Document]:
    if not is_configured():
        return []

    query = jql or config.JIRA_JQL
    payload = {
        "jql": query,
        "maxResults": 500,
        "fields": _SEARCH_FIELDS,
    }
    try:
        data = _jira_request("/rest/api/3/search/jql", payload)
    except urllib.error.HTTPError as ex:
        raise RuntimeError(f"JIRA HTTP {ex.code}: {ex.read().decode()[:300]}") from ex
    except urllib.error.URLError as ex:
        raise RuntimeError(f"JIRA unreachable: {ex.reason}") from ex

    docs: list[Document] = []
    for issue in data.get("issues", []):
        docs.append(_format_issue(issue))
    return docs
