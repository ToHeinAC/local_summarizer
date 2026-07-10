"""Summary template registry. Plain python, no LangChain.

``label`` and ``description`` are German — they are shown in the UI. Each
template's ``structure`` string stays English: it is injected into
FINALIZE_PROMPT to steer the summary's format and information density.
"""

from __future__ import annotations

TEMPLATES: list[dict] = [
    {
        "id": "executive",
        "label": "Management (knapp)",
        "description": "Überblick in 3-5 Sätzen für Entscheider.",
        "structure": (
            "A single short paragraph of 3-5 sentences capturing only the most "
            "important conclusions. No headings, no lists."
        ),
    },
    {
        "id": "standard",
        "label": "Standard",
        "description": "Ausgewogene Zusammenfassung mit kurzem Überblick und Kernpunkten.",
        "structure": (
            "A '## Overview' section (2-4 sentences) followed by a "
            "'## Key Points' section with 4-8 concise bullet points."
        ),
    },
    {
        "id": "detailed",
        "label": "Ausführlich",
        "description": "Abschnittsweise Zusammenfassung, die die Struktur erhält.",
        "structure": (
            "A '## Summary' overview, then one '### ' subsection per major "
            "topic in the document, each with 5-15 sentences. End with a "
            "'## Conclusion' section."
        ),
    },
    {
        "id": "bullets",
        "label": "Stichpunkte",
        "description": "Einfache Liste der wichtigsten Erkenntnisse.",
        "structure": (
            "Only a Markdown bullet list of 6-20 key takeaways. "
            "No headings, no prose paragraphs."
        ),
    },
    {
        "id": "action_items",
        "label": "Maßnahmen",
        "description": "Entscheidungen und nächste Schritte als Aufgaben.",
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
