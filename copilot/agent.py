"""Main agent: Claude API calls for PRD generation and ticket creation."""

import os
from anthropic import Anthropic
from dotenv import load_dotenv
from .prompts import (
    SYSTEM_PROMPT,
    SYSTEM_PROMPT_NO_RAG,
    PRD_USER_PROMPT,
    PRD_USER_PROMPT_WITH_RAG,
    LINEAR_TICKET_PROMPT,
    TICKET_PROMPT_WITH_RAG,
)

load_dotenv()


def get_client():
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key or api_key == "your-api-key-here":
        raise ValueError(
            "ANTHROPIC_API_KEY not set. Copy .env.example to .env and add your key."
        )
    return Anthropic(api_key=api_key)


def generate_prd(topic: str, retrieved_chunks: str = "", context: str = "", domain_chunks: str = "") -> str:
    """Generate a PRD using Claude, optionally with RAG-retrieved style examples and domain knowledge."""
    client = get_client()

    domain_context = ""
    if domain_chunks:
        domain_context = (
            "Here is relevant domain knowledge about the industry and workflows. "
            "Use this to ensure technical accuracy, realistic data flows, compliance details, and edge cases:\n\n"
            f"---\n{domain_chunks}\n---\n\n"
        )

    if retrieved_chunks:
        system = SYSTEM_PROMPT
        user_message = PRD_USER_PROMPT_WITH_RAG.format(
            topic=topic,
            retrieved_chunks=retrieved_chunks,
            domain_context=domain_context,
            context=context or "No additional context provided.",
        )
    else:
        system = SYSTEM_PROMPT_NO_RAG
        user_message = PRD_USER_PROMPT.format(
            topic=topic,
            context=(domain_context + (context or "No additional context provided.")),
        )

    response = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=4096,
        system=system,
        messages=[{"role": "user", "content": user_message}],
    )

    return response.content[0].text


def generate_tickets(prd_section: str, retrieved_chunks: str = "") -> str:
    """Break a PRD section into tickets, optionally matching ticket style via RAG."""
    client = get_client()

    if retrieved_chunks:
        prompt = TICKET_PROMPT_WITH_RAG.format(
            prd_section=prd_section,
            retrieved_chunks=retrieved_chunks,
        )
    else:
        prompt = LINEAR_TICKET_PROMPT.format(prd_section=prd_section)

    response = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=2048,
        messages=[{"role": "user", "content": prompt}],
    )

    return response.content[0].text
