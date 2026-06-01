"""Linear MCP integration for ticket creation (stretch goal)."""

import os
import json
import urllib.request
from dotenv import load_dotenv

load_dotenv()


def get_linear_headers():
    api_key = os.getenv("LINEAR_API_KEY")
    if not api_key or api_key == "your-linear-api-key-here":
        raise ValueError(
            "LINEAR_API_KEY not set. Add it to your .env file."
        )
    return {
        "Authorization": api_key,
        "Content-Type": "application/json",
    }


def create_issue(title: str, description: str, team_id: str, priority: int = 3) -> dict:
    """Create a Linear issue via GraphQL API.

    Priority: 0=none, 1=urgent, 2=high, 3=medium, 4=low
    """
    query = """
    mutation CreateIssue($title: String!, $description: String!, $teamId: String!, $priority: Int) {
        issueCreate(input: {title: $title, description: $description, teamId: $teamId, priority: $priority}) {
            success
            issue {
                id
                identifier
                url
            }
        }
    }
    """

    payload = json.dumps({
        "query": query,
        "variables": {
            "title": title,
            "description": description,
            "teamId": team_id,
            "priority": priority,
        },
    }).encode("utf-8")

    req = urllib.request.Request(
        "https://api.linear.app/graphql",
        data=payload,
        headers=get_linear_headers(),
        method="POST",
    )

    with urllib.request.urlopen(req) as resp:
        result = json.loads(resp.read().decode())

    if "errors" in result:
        raise RuntimeError(f"Linear API error: {result['errors']}")

    return result["data"]["issueCreate"]["issue"]


def list_teams() -> list[dict]:
    """List available Linear teams (needed to get team_id)."""
    query = """
    query { teams { nodes { id name key } } }
    """

    payload = json.dumps({"query": query}).encode("utf-8")

    req = urllib.request.Request(
        "https://api.linear.app/graphql",
        data=payload,
        headers=get_linear_headers(),
        method="POST",
    )

    with urllib.request.urlopen(req) as resp:
        result = json.loads(resp.read().decode())

    return result["data"]["teams"]["nodes"]
