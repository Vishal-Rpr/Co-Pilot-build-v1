"""Prototype generation: spec + HTML mockup from a topic or existing PRD."""

import os
from pathlib import Path

from .agent import get_client
from .prompts import (
    PROTOTYPE_SPEC_PROMPT,
    PROTOTYPE_SPEC_USER_PROMPT,
    PROTOTYPE_SPEC_USER_PROMPT_FROM_PRD,
    PROTOTYPE_HTML_PROMPT,
)


def generate_prototype_spec(
    topic: str = "",
    prd_content: str = "",
    retrieved_chunks: str = "",
    context: str = "",
) -> str:
    """Generate a prototype spec from a topic or an existing PRD."""
    client = get_client()

    if prd_content:
        user_message = PROTOTYPE_SPEC_USER_PROMPT_FROM_PRD.format(
            prd_content=prd_content,
            context=context or "",
        )
    else:
        user_message = PROTOTYPE_SPEC_USER_PROMPT.format(
            topic=topic,
            context=context or "",
        )

    if retrieved_chunks:
        user_message += (
            "\n\nHere are examples of how the user writes prototype specs. "
            "Match their structure:\n\n---\n"
            f"{retrieved_chunks}\n---"
        )

    response = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=2048,
        system=PROTOTYPE_SPEC_PROMPT,
        messages=[{"role": "user", "content": user_message}],
    )

    return response.content[0].text


def generate_prototype_html(spec: str) -> str:
    """Generate a self-contained HTML prototype from a spec."""
    client = get_client()

    response = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=16384,
        messages=[
            {"role": "user", "content": PROTOTYPE_HTML_PROMPT.format(spec=spec)}
        ],
    )

    html = response.content[0].text

    if not html.strip().startswith("<!DOCTYPE") and not html.strip().startswith("<html"):
        start = html.find("<!DOCTYPE")
        if start == -1:
            start = html.find("<html")
        if start != -1:
            html = html[start:]

    end = html.rfind("</html>")
    if end != -1:
        html = html[: end + len("</html>")]

    return html


def save_prototype(output_dir: str, spec: str = "", html: str = "") -> dict:
    """Save prototype files to the output directory. Returns paths of saved files."""
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)

    saved = {}

    if spec:
        spec_path = out / "spec.md"
        spec_path.write_text(spec, encoding="utf-8")
        saved["spec"] = str(spec_path)

    if html:
        html_path = out / "index.html"
        html_path.write_text(html, encoding="utf-8")
        saved["html"] = str(html_path)

    return saved
