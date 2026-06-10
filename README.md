# PM Co-pilot

## Overview

A RAG-powered CLI tool that helps product managers write PRDs, generate tracker-ready tickets, build clickable UI prototypes, visualize workflows in Excalidraw, and publish docs to Confluence — all in the user's personal writing style.

## Goals

- Match the user's writing voice from their own reference documents, not generic AI templates
- Support the full PM artifact workflow: PRD → eval → prototype → tickets → publish
- Keep integrations lightweight (REST/GraphQL, no heavy SDKs) so the tool stays portable and auditable
- Make quality measurement explicit via a built-in eval rubric before sharing with stakeholders

## Non-goals

- Replacing a conversational agent or web UI (CLI first; interactive mode is planned)
- Fine-tuning models on user data (RAG is the style-matching approach)
- Shipping as a hosted SaaS product (local, open-source tool for PMs who want control)

---

## Setup

1. Clone this repo
2. Create a virtual environment:
   ```
   python -m venv venv
   venv\Scripts\activate
   ```
3. Install dependencies:
   ```
   pip install -r requirements.txt
   ```
4. Copy `.env.example` to `.env` and add your API keys:
   ```
   copy .env.example .env
   ```
5. Add reference PRDs to `reference_docs/`, tickets to `reference_tickets/`, prototype specs to `reference_prototypes/`
6. Ingest your reference docs:
   ```
   python -m copilot ingest
   ```

## Usage

```bash
# Generate a PRD matching your writing style
python -m copilot generate "credit limit enforcement for B2B clients" -o credit-limit-prd.md

# Generate and auto-evaluate in one shot
python -m copilot generate "shipment tracking" --eval

# Generate without RAG (generic template)
python -m copilot generate "feature name" --no-rag

# Evaluate any PRD or spec against the quality rubric
python -m copilot eval credit-limit-prd.md

# Break a PRD into tickets (default: Linear format)
python -m copilot tickets credit-limit-prd.md

# Break a PRD into Jira tickets
python -m copilot tickets credit-limit-prd.md --target jira

# Generate an Excalidraw architecture diagram
python -m copilot diagram "credit limit sync flow" -o credit-flow.excalidraw

# Generate a UI prototype from a PRD (spec + clickable HTML)
python -m copilot prototype --from credit-limit-prd.md -o prototype/

# Generate a prototype from a topic
python -m copilot prototype "shipment tracking dashboard" -o prototype/

# Publish a PRD to Confluence
python -m copilot publish credit-limit-prd.md --to confluence --space PM
```

---

## What happens today

PMs using generic AI tools get templatized output that doesn't match their voice or team's conventions. Turning a PRD into tickets, diagrams, prototypes, and published docs is a separate manual process every time. There's no built-in way to ask "is this good enough to share?"

## What this changes

You drop reference documents into `reference_docs/`, `reference_tickets/`, and `reference_prototypes/`. The co-pilot ingests them, retrieves relevant chunks at generation time, and produces output structurally aligned with your past work. Eval scores artifacts before you ship. Prototype and diagram commands extend the same pipeline from document to demo.

---

## Architecture

| Component | What it does |
|-----------|--------------|
| **LLM** | Claude Sonnet 4.6 (Anthropic API) |
| **RAG** | ChromaDB local vector store with `doc_type` filtering (`prd` \| `ticket` \| `prototype`) |
| **Integrations** | Linear (GraphQL), Jira (REST v3), Confluence (REST), Excalidraw (JSON export) |
| **CLI** | Click-based command interface |
| **Pattern** | Lightweight REST/GraphQL via urllib; API keys from `.env`. No SDKs. |

---

## Project structure

```
copilot/
  __main__.py          CLI entry point. Commands: ingest, generate, eval, prototype, tickets, diagram, publish
  agent.py             Claude API calls (generate_prd, generate_tickets)
  eval.py              5-dimension quality rubric evaluation
  prototype.py         Prototype spec + HTML generation from topics or PRDs
  rag.py               ChromaDB ingestion + retrieval with doc_type filtering
  prompts.py           System/user prompts and templates
  excalidraw.py        Excalidraw JSON diagram generation
  linear_mcp.py        Linear GraphQL integration
  jira_client.py       Jira REST API v3 integration
  confluence_client.py Confluence REST API integration
reference_docs/        Example PRDs for RAG style matching
reference_tickets/     Past tickets for ticket style matching
reference_prototypes/  Past prototype specs for prototype style matching
tests/
  test_rag.py          pytest tests for chunking, ingestion, and retrieval
```

---

## Key considerations

- **Style matching is reference-driven.** The system prompt is adaptive — it reverse-engineers patterns from whatever docs you provide, not hardcoded section names.
- **Eval is opt-in.** Every eval is an API call; use `--eval` on generate or run `eval` standalone when you want a quality gate.
- **Prototype output is single-file HTML.** No dependencies; opens in any browser. Spec + HTML written to the output directory.
- **Cost.** Sonnet at personal use volume (5–20 PRDs/week) typically stays under a few dollars/month.

---

## Open questions / roadmap

| Phase | Scope |
|-------|--------|
| **v1 (current)** | CLI: RAG, generate, eval, prototype, tickets, diagram, publish |
| **v2** | Interactive mode — multi-turn refinement with session context |
| **v3** | Web UI or plugin for non-technical PMs |

**Upcoming:** Google Docs publishing (`--to googledocs`), customizable eval rubric (YAML), more integration targets.

---

## Success metrics (for this project)

- Style consistency scores on eval (target: 4+/5 when reference docs are ingested)
- End-to-end workflow usable without editing the core Python modules
- Repo readable as a portfolio piece: architecture story + working commands + tests passing

---

## Author

Vishal Prabhakar — Senior Product Manager in B2B freight forwarding, building AI product tools.
