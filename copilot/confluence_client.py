"""Confluence integration: create pages and list spaces via REST API v2."""

import os
import json
import base64
import urllib.request
from dotenv import load_dotenv

load_dotenv()


def _get_auth():
    """Build basic auth header from email + API token."""
    base_url = os.getenv("CONFLUENCE_BASE_URL", "").rstrip("/")
    email = os.getenv("CONFLUENCE_EMAIL", "")
    token = os.getenv("CONFLUENCE_API_TOKEN", "")

    if not all([base_url, email, token]):
        raise ValueError(
            "Confluence credentials not set. Add CONFLUENCE_BASE_URL, "
            "CONFLUENCE_EMAIL, and CONFLUENCE_API_TOKEN to your .env file."
        )

    credentials = base64.b64encode(f"{email}:{token}".encode()).decode()
    headers = {
        "Authorization": f"Basic {credentials}",
        "Content-Type": "application/json",
        "Accept": "application/json",
    }
    return base_url, headers


def _markdown_to_storage_format(markdown_text: str) -> str:
    """Minimal markdown-to-Confluence storage format conversion.

    Handles headings, bold, bullet lists, and code blocks. For full fidelity,
    consider using a dedicated converter library.
    """
    import re

    lines = markdown_text.split("\n")
    html_lines = []
    in_list = False
    in_code = False

    for line in lines:
        if line.strip().startswith("```"):
            if in_code:
                html_lines.append("</ac:plain-text-body></ac:structured-macro>")
                in_code = False
            else:
                html_lines.append(
                    '<ac:structured-macro ac:name="code">'
                    "<ac:plain-text-body><![CDATA["
                )
                in_code = True
            continue

        if in_code:
            html_lines.append(line)
            continue

        if line.startswith("# "):
            html_lines.append(f"<h1>{line[2:]}</h1>")
        elif line.startswith("## "):
            html_lines.append(f"<h2>{line[3:]}</h2>")
        elif line.startswith("### "):
            html_lines.append(f"<h3>{line[4:]}</h3>")
        elif line.strip().startswith("- "):
            if not in_list:
                html_lines.append("<ul>")
                in_list = True
            content = line.strip()[2:]
            content = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", content)
            html_lines.append(f"<li>{content}</li>")
        else:
            if in_list:
                html_lines.append("</ul>")
                in_list = False
            content = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", line)
            if content.strip():
                html_lines.append(f"<p>{content}</p>")

    if in_list:
        html_lines.append("</ul>")

    return "\n".join(html_lines)


def create_page(
    title: str,
    body_markdown: str,
    space_key: str,
    parent_id: str | None = None,
) -> dict:
    """Create a Confluence page from markdown content.

    Converts markdown to Confluence storage format before posting.
    Returns dict with id, title, and URL.
    """
    base_url, headers = _get_auth()

    body_html = _markdown_to_storage_format(body_markdown)

    payload_dict = {
        "type": "page",
        "title": title,
        "space": {"key": space_key},
        "body": {
            "storage": {
                "value": body_html,
                "representation": "storage",
            }
        },
    }

    if parent_id:
        payload_dict["ancestors"] = [{"id": parent_id}]

    payload = json.dumps(payload_dict).encode("utf-8")

    req = urllib.request.Request(
        f"{base_url}/wiki/rest/api/content",
        data=payload,
        headers=headers,
        method="POST",
    )

    with urllib.request.urlopen(req) as resp:
        result = json.loads(resp.read().decode())

    return {
        "id": result["id"],
        "title": result["title"],
        "url": f"{base_url}/wiki{result['_links']['webui']}",
    }


def list_spaces() -> list[dict]:
    """List available Confluence spaces (key, name)."""
    base_url, headers = _get_auth()

    req = urllib.request.Request(
        f"{base_url}/wiki/rest/api/space",
        headers=headers,
        method="GET",
    )

    with urllib.request.urlopen(req) as resp:
        result = json.loads(resp.read().decode())

    return [
        {"key": s["key"], "name": s["name"]}
        for s in result.get("results", [])
    ]
