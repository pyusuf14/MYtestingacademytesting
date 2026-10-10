# QABuddy.ai

Self-hosted **Hybrid RAG** for QA engineers. Ingests code, docs, test cases,
PRDs, JIRA tickets (live + exported), logs, meeting notes and diagrams into a
local **Qdrant** vector store with **BGE** embeddings, then serves grounded,
**cited answers** through a FastAPI chatbot.

## Stack (all open source)

| Concern | Choice |
|---|---|
| Embeddings | `BAAI/bge-small-en-v1.5` (FastEmbed/ONNX, 384-dim) |
| Vector DB | Qdrant (embedded local mode, dense + sparse hybrid) |
| Retrieval | Dense (BGE) + sparse (keyword) with Reciprocal Rank Fusion |
| Chatbot | FastAPI + Uvicorn |
| JIRA | Atlassian Cloud REST v3 via PAT (Basic auth) |

## Setup

```powershell
cd QABUDDY\qabuddy
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

Configure `.env` (see `.env.example`). JIRA creds are already in `.env`
(gitignored).

## Usage

```powershell
# Ingest everything (local + live JIRA) and build the index
python -m qabuddy.pipeline ingest

# One-shot question
python -m qabuddy.pipeline ask "Why did login tests fail on build 142?"

# Start the chatbot API on http://localhost:8000
python -m qabuddy.pipeline serve
```

API:

```powershell
curl.exe -X POST http://localhost:8000/ask `
  -H "Content-Type: application/json" `
  -d '{\"question\":\"What test cases cover the login page?\"}'
```

## Source folders ingested

`Company Docs`, `JIRA tickets`, `Lucid charts`, `PRD`, `Testcases`,
`jenkins log`, `meeting notes`, `sourcecodes`. (`figma designs` is Phase 2.)

## Memory footprint (bge-small)

- Disk: ~130 MB model + ~500–700 MB venv deps + tiny Qdrant data
- RAM: ~450–600 MB at launch, ~800 MB–1 GB peak during indexing
