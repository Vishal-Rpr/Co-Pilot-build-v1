"""Jira integration: create issues and list projects via REST API v3."""

import os
import json
import base64
import urllib.request
from dotenv import load_dotenv

load_dotenv()


def _get_auth():
    """Build basic auth header from email + API token."""
    base_url = os.getenv("JIRA_BASE_URL", "").rstrip("/")
    email = os.getenv("JIRA_EMAIL", "")
    token = os.getenv("JIRA_API_TOKEN", "")

    if not all([base_url, email, token]):
        raise ValueError(
            "Jira credentials not set. Add JIRA_BASE_URL, JIRA_EMAIL, "
            "and JIRA_API_TOKEN to your .env file."
        )

    credentials = base64.b64encode(f"{email}:{token}".encode()).decode()
    headers = {
        "Authorization": f"Basic {credentials}",
        "Content-Type": "application/json",
        "Accept": "application/json",
    }
    return base_url, headers


def create_issue(
    summary: str,
    description: str,
    project_key: str,
    issue_type: str = "Story",
    priority: str = "Medium",
) -> dict:
    """Create a Jira issue via REST API v3.

    Returns dict with id, key, and self URL.
    """
    base_url, headers = _get_auth()

    payload = json.dumps({
        "fields": {
            "project": {"key": project_key},
            "summary": summary,
            "description": {
                "type": "doc",
                "version": 1,
                "content": [
                    {
                        "type": "paragraph",
                        "content": [{"type": "text", "text": description}],
                    }
                ],
            },
            "issuetype": {"name": issue_type},
            "priority": {"name": priority},
        }
    }).encode("utf-8")

    req = urllib.request.Request(
        f"{base_url}/rest/api/3/issue",
        data=payload,
        headers=headers,
        method="POST",
    )

    with urllib.request.urlopen(req) as resp:
        result = json.loads(resp.read().decode())

    return {
        "id": result["id"],
        "key": result["key"],
        "url": f"{base_url}/browse/{result['key']}",
    }


def list_projects() -> list[dict]:
    """List available Jira projects (key, name, id)."""
    base_url, headers = _get_auth()

    req = urllib.request.Request(
        f"{base_url}/rest/api/3/project",
        headers=headers,
        method="GET",
    )

    with urllib.request.urlopen(req) as resp:
        projects = json.loads(resp.read().decode())

    return [{"id": p["id"], "key": p["key"], "name": p["name"]} for p in projects]
