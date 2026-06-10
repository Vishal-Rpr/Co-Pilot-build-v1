# PM Co-pilot v0

A RAG-powered CLI tool that helps product managers write PRDs, generate tracker-ready tickets, build clickable UI prototypes, visualize workflows in Excalidraw, and publish docs to Confluence -- all in the user's personal writing style.

> **Disclaimer:** The sample documents in `reference_docs/` and `reference_prototypes/` are illustrative examples for demonstrating style-matching only. They use a fictional B2B freight context and contain no company-specific, confidential, or proprietary data; any cost figures are rough estimates, not actual vendor pricing.

## Problem

Generic AI tools produce cookie-cutter output that doesn't match your voice or your team's conventions. You end up rewriting most of it anyway. And once you have a PRD, turning it into tickets, diagrams, and published docs is a separate manual process every time.

## Solution

PM Co-pilot uses RAG (Retrieval-Augmented Generation) to learn your writing style from reference documents you provide. It retrieves relevant sections from your past PRDs, tickets, and prototype specs, uses them as style examples for Claude, and produces output that sounds like you. Then it pushes that output wherever you need it -- Linear, Jira, Confluence, Excalidraw, or a clickable HTML prototype.

## Architecture

- **LLM:** Claude (Sonnet 4.6, via Anthropic API)
- **RAG:** ChromaDB local vector store with doc_type filtering (PRDs and tickets stored separately)
- **Integrations:** Linear (GraphQL), Jira (REST v3), Confluence (REST), Excalidraw (JSON export)
- **CLI:** Click-based command interface
- **Pattern:** All integrations use lightweight REST/GraphQL via urllib with API keys from `.env`. No SDKs.

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
5. Add reference PRDs to `reference_docs/` and past tickets to `reference_tickets/`
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
python -m copilot diagram "credit limit and QuickBooks sync flow" -o credit-flow.excalidraw

# Generate a UI prototype from a PRD (spec + clickable HTML)
python -m copilot prototype --from credit-limit-prd.md -o prototype/

# Generate a prototype from a topic
python -m copilot prototype "shipment tracking dashboard" -o prototype/

# Publish a PRD to Confluence
python -m copilot publish credit-limit-prd.md --to confluence --space PM
```

## Project Structure

```
copilot/
  __main__.py          CLI entry point (Click). Commands: ingest, generate, eval, prototype, tickets, diagram, publish
  agent.py             Claude API calls (generate_prd, generate_tickets)
  eval.py              5-dimension quality rubric evaluation
  prototype.py         Prototype spec + HTML generation from topics or PRDs
  rag.py               ChromaDB ingestion + retrieval with doc_type filtering (prd | ticket | prototype)
  prompts.py           All system/user prompts and templates
  excalidraw.py        Excalidraw JSON diagram generation
  linear_mcp.py        Linear GraphQL API integration
  jira_client.py       Jira REST API v3 integration
  confluence_client.py Confluence REST API integration
reference_docs/        Your example PRDs for RAG style matching
reference_tickets/     Your past tickets for ticket style matching
reference_prototypes/  Your past prototype specs for prototype style matching
tests/
  test_rag.py          13 pytest tests for chunking, ingestion, and retrieval
```

## Design decisions

- **RAG over fine-tuning** — Works with 2–3 reference docs; no training cost or hundreds of examples required
- **Opt-in eval** — Every eval is an API call; default stays cheap and fast; users score when they want a quality gate
- **Adaptive style matching** — The system prompt reverse-engineers patterns from whatever references you provide, not hardcoded section names
- **Lightweight integrations** — REST/GraphQL using API keys
- **CLI first** — Validates the pipeline before investing in conversational UI or a web front-end

## Roadmap

This is a CLI tool by design -- it validates the core AI pipeline with the least build effort. The progression:

1. **CLI** (current) -- prove the engine works: RAG, generation, eval, integrations
2. **Interactive mode** (next) -- multi-turn conversational PRD refinement in the terminal, with session context
3. **Web UI / plugin** (future) -- the interface non-technical PMs would actually use day-to-day

### Upcoming

- **Interactive mode:** Conversational session with memory -- "generate a PRD", "beef up the metrics", "now create tickets from section 3"
- **Google Docs publishing:** `--to googledocs` flag on the publish command
- **Customizable eval rubric:** Load scoring dimensions from a YAML file instead of hardcoded prompt

## Author

Vishal Prabhakar -- Senior Product Manager in B2B freight forwarding, building AI product tools.
