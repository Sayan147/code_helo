"""
Documentation Generation Agent.
Generates code documentation, API docs, README files, and inline comments.
"""

import logging
from typing import Any, Dict, List

from app.utils.llm import call_llm

logger = logging.getLogger(__name__)


def generate_documentation(
    requirement: str,
    project_type: str,
    code: str = "",
    exemplars: List[Dict[str, Any]] = None,
    tribal_kb: Dict[str, Any] = None,
) -> Dict[str, Any]:
    """
    Generate documentation for code or project.
    
    Args:
        requirement: User requirement for documentation
        project_type: Project type identifier
        code: Optional code to document
        exemplars: Optional documentation exemplars from KB
        tribal_kb: Optional tribal knowledge base
        
    Returns:
        Dictionary with different types of documentation (readme, api_docs, inline_docs, etc.)
    """
    if exemplars is None:
        exemplars = []
    if tribal_kb is None:
        tribal_kb = {}
    
    exemplars_text = ""
    if exemplars:
        exemplars_text = "\n".join([
            f"# Exemplar: {ex.get('section_name', '')}\n{ex.get('description', '')}\n"
            for ex in exemplars[:3]
        ])
    
    tribal_summary = ""
    if tribal_kb:
        import json
        try:
            tribal_summary = json.dumps(tribal_kb, indent=2)[:2000]
        except Exception:
            tribal_summary = str(tribal_kb)[:2000]
    
    prompt_parts = [
        "You are a technical writer. Generate comprehensive documentation.",
        "",
        f"PROJECT_TYPE: {project_type}",
        "",
        "REQUIREMENT:",
        requirement,
    ]
    
    if code:
        prompt_parts.extend([
            "",
            "CODE TO DOCUMENT:",
            code,
        ])
    
    if exemplars_text:
        prompt_parts.extend([
            "",
            "DOCUMENTATION EXEMPLARS:",
            exemplars_text,
        ])
    
    if tribal_summary:
        prompt_parts.extend([
            "",
            "TRIBAL KNOWLEDGE:",
            tribal_summary,
        ])
    
    prompt_parts.extend([
        "",
        "Generate documentation including:",
        "- README with setup and usage",
        "- API documentation",
        "- Inline code comments",
        "- Usage examples",
        "",
        "Return JSON with this shape ONLY:",
        "{",
        '  "readme": "...",',
        '  "api_docs": "...",',
        '  "inline_docs": "...",',
        '  "usage_examples": "...",',
        '  "installation_instructions": "..."',
        "}",
    ])
    
    prompt = "\n".join(prompt_parts)
    
    try:
        raw = call_llm(prompt) or ""
    except Exception as exc:
        logger.error("Documentation generation failed: %s", exc)
        return {
            "readme": "",
            "api_docs": "",
            "inline_docs": "",
            "usage_examples": "",
            "installation_instructions": "",
        }
    
    import json
    
    try:
        # Extract JSON block
        start = raw.find("{")
        end = raw.rfind("}")
        if start != -1 and end != -1:
            json_block = raw[start:end+1]
            parsed = json.loads(json_block)
            if isinstance(parsed, dict):
                return parsed
    except Exception as exc:
        logger.warning("Failed to parse documentation response: %s", exc)
    
    return {
        "readme": "",
        "api_docs": "",
        "inline_docs": "",
        "usage_examples": "",
        "installation_instructions": "",
    }
