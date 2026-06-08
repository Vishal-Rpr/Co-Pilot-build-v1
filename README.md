# PM Co-pilot v0

An AI agent that helps product managers write PRDs, generate user stories, and visualize workflows in Excalidraw - in the users style of writing

## Problem

Generic AI tools produce cookie-cutter output that doesn't match your voice or your team's conventions. You end up rewriting most of it anyway.

## Solution

PM Co-pilot uses RAG (Retrieval-Augmented Generation) to learn your writing style from reference PRDs you provide. When you ask it to write a new PRD, it retrieves relevant sections from your past work and uses them as style examples for Claude, producing output that sounds like you.

## Architecture

- **LLM:** Claude (via Anthropic API)
- **RAG:** ChromaDB (local vector store) for style-matching retrieval
- **MCP:** Linear integration for ticket creation
- **CLI:** Click-based command interface

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
5. Add 1-3 reference PRDs (markdown files) to `reference_docs/`
6. Ingest your reference docs:
   ```
   python -m copilot ingest
   ```
7. Generate a PRD:
   ```
   python -m copilot generate "credit limit enforcement for B2B clients"
   ```

## Project Structure

```
copilot/
  __init__.py     - Package init
  agent.py        - Main agent loop (Claude + tool routing)
  rag.py          - Embed and retrieve from reference PRDs
  linear_mcp.py   - Linear ticket creation via MCP
  prompts.py      - System prompts and templates
reference_docs/   - Your example PRDs (for RAG style matching)
tests/            - Test scenarios for evaluation
```

## What This Demonstrates

- RAG pipeline: chunking, embedding, similarity search, retrieval
- Claude API: system prompts, structured generation, tool use
- MCP integration: connecting LLMs to external tools
- AI product evaluation: measuring output quality against reference style
