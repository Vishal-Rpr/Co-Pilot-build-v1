"""Excalidraw export: generate .excalidraw diagram files from feature descriptions."""

import json
from .agent import get_client
from .prompts import EXCALIDRAW_PROMPT


def generate_diagram(feature_description: str) -> str:
    """Call Claude to produce a valid Excalidraw JSON for the given feature.

    Returns the raw JSON string ready to write to a .excalidraw file.
    """
    client = get_client()

    response = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=4096,
        messages=[
            {
                "role": "user",
                "content": EXCALIDRAW_PROMPT.format(
                    feature_description=feature_description
                ),
            }
        ],
    )

    raw = response.content[0].text

    # Extract JSON from the response (Claude may wrap it in markdown code fences)
    if "```" in raw:
        lines = raw.split("\n")
        json_lines = []
        inside_block = False
        for line in lines:
            if line.strip().startswith("```"):
                inside_block = not inside_block
                continue
            if inside_block:
                json_lines.append(line)
        raw = "\n".join(json_lines)

    # Validate it's parseable JSON
    parsed = json.loads(raw)
    return json.dumps(parsed, indent=2)
