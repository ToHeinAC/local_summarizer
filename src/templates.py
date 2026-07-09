"""Summary template registry. Plain python, no LangChain.

Each template's ``structure`` string is injected into FINALIZE_PROMPT to steer
the summary's format and information density.
"""

from __future__ import annotations

TEMPLATES: list[dict] = [
    {
        "id": "executive",
        "label": "Executive (terse)",
        "description": "3-5 sentence high-level overview for decision makers.",
        "structure": (
            "A single short paragraph of 3-5 sentences capturing only the most "
            "important conclusions. No headings, no lists."
        ),
    },
    {
        "id": "standard",
        "label": "Standard",
        "description": "Balanced summary with a short overview and key points.",
        "structure": (
            "A '## Overview' section (2-4 sentences) followed by a "
            "'## Key Points' section with 4-8 concise bullet points."
        ),
    },
    {
        "id": "detailed",
        "label": "Detailed",
        "description": "Section-by-section summary preserving structure.",
        "structure": (
            "A '## Summary' overview, then one '### ' subsection per major "
            "topic in the document, each with 2-4 sentences. End with a "
            "'## Conclusion' section."
        ),
    },
    {
        "id": "bullets",
        "label": "Bullet key-points",
        "description": "Flat list of the most important takeaways.",
        "structure": (
            "Only a Markdown bullet list of 6-12 key takeaways. "
            "No headings, no prose paragraphs."
        ),
    },
    {
        "id": "action_items",
        "label": "Action items",
        "description": "Decisions and next steps extracted as tasks.",
        "structure": (
            "A '## Decisions' bullet list and a '## Action Items' bullet list. "
            "Each action item starts with a verb. Omit a section if empty."
        ),
    },
]

DEFAULT_TEMPLATE_ID = "standard"


def list_templates() -> list[dict]:
    """Return all registered templates."""
    return TEMPLATES


def get_template(template_id: str) -> dict:
    """Return the template entry for ``template_id``; raise KeyError if unknown."""
    for template in TEMPLATES:
        if template["id"] == template_id:
            return template
    raise KeyError(f"Unknown template id: {template_id}")
