"""Eval module: score AI-generated PM artifacts against a 5-dimension rubric."""

import re
from .agent import get_client
from .prompts import EVAL_PROMPT, EVAL_USER_PROMPT, EVAL_USER_PROMPT_WITH_REF


def evaluate_document(document: str, retrieved_chunks: str = "") -> dict:
    """Score a document on completeness, domain accuracy, actionability,
    style consistency, and metric specificity. Returns raw scorecard text
    and parsed scores."""
    client = get_client()

    if retrieved_chunks:
        user_message = EVAL_USER_PROMPT_WITH_REF.format(
            document=document,
            retrieved_chunks=retrieved_chunks,
        )
    else:
        user_message = EVAL_USER_PROMPT.format(document=document)

    response = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=2048,
        system=EVAL_PROMPT,
        messages=[{"role": "user", "content": user_message}],
    )

    scorecard = response.content[0].text
    scores = _parse_scores(scorecard)

    return {
        "scorecard": scorecard,
        "scores": scores,
        "total": scores.get("total", 0),
        "verdict": scores.get("verdict", "Unknown"),
    }


def _parse_scores(scorecard: str) -> dict:
    """Extract individual dimension scores, total, and verdict from the
    scorecard markdown."""
    scores = {}

    dimension_pattern = re.compile(
        r"\|\s*(Completeness|Domain accuracy|Actionability|Style consistency|Metric specificity)"
        r"\s*\|\s*(\d+|N/A)/?\d*\s*\|"
    )
    for match in dimension_pattern.finditer(scorecard):
        name = match.group(1).lower().replace(" ", "_")
        raw = match.group(2)
        scores[name] = int(raw) if raw != "N/A" else None

    total_match = re.search(r"\*\*Total:\s*(\d+)/25\*\*", scorecard)
    if total_match:
        scores["total"] = int(total_match.group(1))

    verdict_match = re.search(
        r"\*\*Verdict:\s*(Ship it|Polish|Rework|Start over)\*\*", scorecard
    )
    if verdict_match:
        scores["verdict"] = verdict_match.group(1)

    return scores
