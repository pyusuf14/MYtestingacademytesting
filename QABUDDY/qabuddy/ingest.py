"""Ingestion: parse each source file into Document objects.

Per-source handling:
- docs          : .md, .pdf (prose, standards, PRDs)
- testcases     : double-encoded CSV (one row == one test case)
- jira_export   : .md JIRA ticket exports (one file == one ticket)
- code          : .zip archives of Selenium/Playwright frameworks
- logs          : .log and .xml (Jenkins/TestNG build logs)
- meeting       : .txt, .md, .vtt (meeting notes / transcripts)
- diagram       : .csv, .json, .txt (Lucid chart exports)
"""
from __future__ import annotations

import csv
import io
import json
import re
import zipfile
from pathlib import Path

from .models import Document


# --------------------------------------------------------------------------
# Low-level text extraction
# --------------------------------------------------------------------------

def _read_text(path: Path) -> str:
    for enc in ("utf-8-sig", "utf-8", "latin-1"):
        try:
            return path.read_text(encoding=enc)
        except UnicodeDecodeError:
            continue
    return path.read_text(encoding="utf-8", errors="replace")


def _extract_pdf(path: Path) -> str:
    from pypdf import PdfReader

    reader = PdfReader(str(path))
    parts = []
    for page in reader.pages:
        try:
            parts.append(page.extract_text() or "")
        except Exception:
            parts.append("")
    return "\n".join(parts).strip()


def _extract_zip_text(path: Path) -> dict[str, str]:
    """Return {filename: text} for text-ish files inside a zip archive."""
    out: dict[str, str] = {}
    text_exts = {".py", ".java", ".js", ".ts", ".json", ".xml", ".md", ".txt",
                 ".yml", ".yaml", ".properties", ".gradle", ".feature"}
    try:
        with zipfile.ZipFile(path) as zf:
            for info in zf.infolist():
                if info.is_dir():
                    continue
                suffix = Path(info.filename).suffix.lower()
                if suffix not in text_exts:
                    continue
                try:
                    out[info.filename] = zf.read(info).decode("utf-8", errors="replace")
                except Exception:
                    continue
    except zipfile.BadZipFile:
        pass
    return out


# --------------------------------------------------------------------------
# Source-specific parsers
# --------------------------------------------------------------------------

def _parse_testcase_csv(path: Path) -> list[Document]:
    """Parse the double-encoded test-case CSV.

    The file's outer layer is CSV where the whole row is a single quoted
    field; that inner string is itself CSV (with a stray leading '?' on the
    header row).
    """
    raw = _read_text(path)
    # Outer pass: each physical line -> one field -> inner CSV string.
    outer = csv.reader(io.StringIO(raw))
    rows: list[list[str]] = []
    header: list[str] = []
    for line in outer:
        if not line:
            continue
        inner = line[0].lstrip("?")
        parsed = next(csv.reader([inner]))
        if not header:
            header = parsed
        else:
            rows.append(parsed)

    docs: list[Document] = []
    for r in rows:
        # Pad/truncate to header length to be safe.
        if len(r) < len(header):
            r = r + [""] * (len(header) - len(r))
        elif len(r) > len(header):
            r = r[: len(header)]
        rec = dict(zip(header, r))

        tid = rec.get("Scenario TID", "").strip()
        desc = rec.get("TestCase Description", "").strip()
        pre = rec.get("PreCondition", "").strip()
        steps = rec.get("TestSteps", "").strip()
        expected = rec.get("Expected Result", "").strip()
        status = rec.get("Status", "").strip()
        priority = rec.get("Priority", "").strip()
        automated = rec.get("Is Automated", "").strip()

        text = "\n".join(
            f"{k}: {v}" for k, v in [
                ("Test Case ID", tid),
                ("Description", desc),
                ("PreCondition", pre),
                ("Test Steps", steps),
                ("Expected Result", expected),
                ("Status", status),
                ("Priority", priority),
                ("Is Automated", automated),
            ] if v
        )
        docs.append(Document(
            source_type="testcases",
            source_path=str(path),
            title=f"{tid} — {desc}" if tid else desc or "Test case",
            text=text,
            metadata={
                "test_id": tid,
                "status": status,
                "priority": priority,
                "automated": automated,
                "citation": f"{tid} (test case)",
            },
        ))
    return docs


def _parse_jira_export_md(path: Path) -> list[Document]:
    raw = _read_text(path)
    # Extract ticket key from filename (Bug_VWO_26.md, QAB-101_..., etc.).
    name = path.stem
    m = re.search(r"\b[A-Z][A-Z0-9]+-\d+\b", name)
    key = m.group(0) if m else (name.split("_")[0] if "_" in name else name)
    title = key
    for line in raw.splitlines():
        if line.strip():
            title = line.strip()
            break
    return [Document(
        source_type="jira_export",
        source_path=str(path),
        title=title,
        text=raw,
        metadata={"ticket_key": key, "citation": key},
    )]


def _parse_lucid_csv(path: Path) -> list[Document]:
    rows = list(csv.reader(io.StringIO(_read_text(path))))
    if not rows:
        return []
    header = rows[0]
    docs: list[Document] = []
    for r in rows[1:]:
        if not any(cell.strip() for cell in r):
            continue
        rec = dict(zip(header, r))
        # A "shape" row has a Text Area 1 value; a "line" row connects shapes.
        if rec.get("Text Area 1", "").strip() or rec.get("Text Area 2", "").strip():
            text = "\n".join(f"{k}: {v}" for k, v in rec.items() if v)
            docs.append(Document(
                source_type="diagram",
                source_path=str(path),
                title=rec.get("Text Area 1") or rec.get("Name") or "Diagram node",
                text=text,
                metadata={"citation": f"{path.stem} (diagram)"},
            ))
    return docs


def _parse_lucid_json(path: Path) -> list[Document]:
    data = json.loads(_read_text(path))
    docs: list[Document] = []
    if isinstance(data, list):
        for item in data:
            text = json.dumps(item, indent=2)
            docs.append(Document(
                source_type="diagram",
                source_path=str(path),
                title=str(item.get("name") or item.get("text") or "Diagram node"),
                text=text,
                metadata={"citation": f"{path.stem} (diagram)"},
            ))
    else:
        docs.append(Document(
            source_type="diagram",
            source_path=str(path),
            title=path.stem,
            text=json.dumps(data, indent=2),
            metadata={"citation": f"{path.stem} (diagram)"},
        ))
    return docs


def _parse_log(path: Path) -> list[Document]:
    raw = _read_text(path)
    return [Document(
        source_type="logs",
        source_path=str(path),
        title=path.name,
        text=raw,
        metadata={"citation": f"{path.name} (log)"},
    )]


def _parse_xml_log(path: Path) -> list[Document]:
    raw = _read_text(path)
    # Strip XML decl and parse testcases for a readable summary, but keep raw too.
    import xml.etree.ElementTree as ET
    try:
        root = ET.fromstring(raw)
        lines = [f"testsuite: {root.attrib.get('name')} "
                 f"tests={root.attrib.get('tests')} failures={root.attrib.get('failures')} "
                 f"errors={root.attrib.get('errors')} skipped={root.attrib.get('skipped')} "
                 f"time={root.attrib.get('time')}"]
        for tc in root.iter("testcase"):
            name = tc.attrib.get("name")
            cls = tc.attrib.get("classname")
            time = tc.attrib.get("time")
            failure = tc.find("failure")
            line = f"testcase: {name} (class: {cls}, time: {time})"
            if failure is not None:
                line += f" -> FAILED: {failure.attrib.get('message', '')} "
                line += (failure.text or "").strip()
            lines.append(line)
        text = "\n".join(lines)
    except ET.ParseError:
        text = raw
    return [Document(
        source_type="logs",
        source_path=str(path),
        title=path.name,
        text=text,
        metadata={"citation": f"{path.name} (test result)"},
    )]


def _parse_vtt(path: Path) -> list[Document]:
    raw = _read_text(path)
    # Parse cue blocks: speaker + text.
    lines = raw.splitlines()
    blocks: list[str] = []
    current: list[str] = []
    for line in lines:
        s = line.strip()
        if not s or s == "WEBVTT":
            if current:
                blocks.append(" ".join(current))
                current = []
            continue
        # Skip cue number and timestamp lines.
        if s.isdigit() or "-->" in s:
            continue
        # Strip speaker tag <v Name> -> Name:
        if s.startswith("<v "):
            name = s[3:].split(">", 1)[0].strip()
            rest = s.split(">", 1)[1].strip() if ">" in s else ""
            s = f"{name}: {rest}"
        current.append(s)
    if current:
        blocks.append(" ".join(current))

    text = "\n".join(blocks)
    return [Document(
        source_type="meeting",
        source_path=str(path),
        title=path.name,
        text=text,
        metadata={"citation": f"{path.name} (transcript)"},
    )]


def _parse_plain(path: Path, source_type: str) -> list[Document]:
    raw = _read_text(path)
    return [Document(
        source_type=source_type,
        source_path=str(path),
        title=path.name,
        text=raw,
        metadata={"citation": f"{path.name}"},
    )]


def _parse_code_zip(path: Path) -> list[Document]:
    files = _extract_zip_text(path)
    docs: list[Document] = []
    for fname, text in files.items():
        if not text.strip():
            continue
        docs.append(Document(
            source_type="code",
            source_path=f"{path.name}/{fname}",
            title=fname,
            text=text,
            metadata={"citation": f"{path.name}:{fname}", "language": Path(fname).suffix.lstrip(".")},
        ))
    return docs


# --------------------------------------------------------------------------
# Dispatch
# --------------------------------------------------------------------------

def parse_file(path: Path, source_type: str) -> list[Document]:
    suffix = path.suffix.lower()

    if source_type == "testcases" and suffix == ".csv":
        return _parse_testcase_csv(path)
    if source_type == "jira_export" and suffix == ".md":
        return _parse_jira_export_md(path)
    if source_type == "diagram":
        if suffix == ".csv":
            return _parse_lucid_csv(path)
        if suffix == ".json":
            return _parse_lucid_json(path)
        return _parse_plain(path, "diagram")
    if source_type == "logs":
        if suffix == ".xml":
            return _parse_xml_log(path)
        return _parse_log(path)
    if source_type == "meeting" and suffix == ".vtt":
        return _parse_vtt(path)
    if source_type == "code" and suffix == ".zip":
        return _parse_code_zip(path)
    if suffix == ".pdf":
        return [Document(
            source_type=source_type,
            source_path=str(path),
            title=path.name,
            text=_extract_pdf(path),
            metadata={"citation": f"{path.name}"},
        )]
    return _parse_plain(path, source_type)
