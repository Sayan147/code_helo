import logging
from typing import Dict, List, Any

from app.utils.llm import call_llm

logger = logging.getLogger(__name__)


def _extract_json_block(raw: str) -> str:
    """Best-effort extraction of a JSON object from a raw LLM string.

    Handles cases where the model wraps the JSON in code fences or adds prose.
    """
    if not raw:
        return ""

    text = raw.strip()

    # Strip markdown fences like ```json ... ```
    if text.startswith("```"):
        # Remove leading ```lang? line
        first_newline = text.find("\n")
        if first_newline != -1:
            text = text[first_newline + 1 :]
        # Strip trailing backticks
        while text.endswith("`"):
            text = text[:-1]
        text = text.strip()

    start = text.find("{")
    end = text.rfind("}")
    if start != -1 and end != -1 and end > start:
        return text[start : end + 1]
    return text


def plan_code_generation(requirements: str, project_type: str) -> Dict[str, Any]:
    """Navigator-style planner for code generation.

    Robust to malformed / non-JSON LLM responses: always returns a valid plan.
    """
    planning_prompt = (
        "You are a senior software architect helping another agent generate code.\n"
        "Given a user requirement and a project type, break the work into a small set "
        "of concrete code components and KB search hints.\n\n"
        "Return JSON with this shape ONLY (no explanations, no markdown, no extra text):\n"
        "{\n"
        '  "components": [\n'
        '    {"name": "...", "description": "...", "priority": 1}\n'
        "  ],\n"
        '  "search_queries": ["...", "..."]\n'
        "}\n\n"
        f"PROJECT_TYPE: {project_type}\n"
        f"REQUIREMENTS:\n{requirements}\n"
    )

    try:
        raw = call_llm(planning_prompt) or ""
    except Exception as exc:  # pragma: no cover - defensive
        logger.error("Navigator planning failed, falling back to default: %s", exc)
        raw = ""

    import json

    # Default safe plan
    plan: Dict[str, Any] = {
        "components": [
            {
                "name": "main_module",
                "description": requirements,
                "priority": 1,
            }
        ],
        "search_queries": [requirements],
    }

    if not raw:
        return plan

    try:
        json_block = _extract_json_block(raw)
        parsed = json.loads(json_block)
        if isinstance(parsed, dict):
            components = parsed.get("components")
            if isinstance(components, list) and components:
                plan["components"] = components
            search_queries = parsed.get("search_queries")
            if isinstance(search_queries, list) and search_queries:
                plan["search_queries"] = search_queries
    except Exception as exc:  # pragma: no cover - defensive
        # Log at info level; we still proceed with fallback plan
        logger.info(
            "Navigator: using fallback plan due to parse issue: %s; raw response (truncated)=%r",
            exc,
            raw[:200],
        )

    return plan


