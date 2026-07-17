"""Summary template registry. Plain python, no LangChain.

``label`` and ``description`` are per-GUI-language dicts (read with
``i18n.pick``). Each template's ``structure`` string stays English: it is
injected into FINALIZE_PROMPT to steer the summary's format and information
density.
"""

from __future__ import annotations

TEMPLATES: list[dict] = [
    {
        "id": "executive",
        "label": {"de": "Management (knapp)", "en": "Executive (terse)"},
        "description": {
            "de": "Überblick in 3-5 Sätzen für Entscheider.",
            "en": "3-5 sentence high-level overview for decision makers.",
        },
        "structure": (
            "A single short paragraph of 3-5 sentences capturing only the most "
            "important conclusions. No headings, no lists."
        ),
    },
    {
        "id": "standard",
        "label": {"de": "Standard", "en": "Standard"},
        "description": {
            "de": "Ausgewogene Zusammenfassung mit kurzem Überblick und Kernpunkten.",
            "en": "Balanced summary with a short overview and key points.",
        },
        "structure": (
            "A '## Overview' section (2-4 sentences) followed by a "
            "'## Key Points' section with 4-8 concise bullet points."
        ),
    },
    {
        "id": "detailed",
        "label": {"de": "Ausführlich", "en": "Detailed"},
        "description": {
            "de": "Abschnittsweise Zusammenfassung, die die Struktur erhält.",
            "en": "Section-by-section summary preserving structure.",
        },
        # MAP_PROMPT and REDUCE_PROMPT carry every identifier through verbatim
        # for the detailed_refs template, so this one must opt out explicitly.
        "structure": (
            "A '## Summary' overview, then one '### ' subsection per major "
            "topic in the document, each with 5-15 sentences. End with a "
            "'## Conclusion' section. Write flowing prose: do not anchor "
            "statements with inline clause, figure, table or document "
            "identifiers; name an identifier only when it is itself the "
            "subject of what you are describing."
        ),
    },
    {
        "id": "detailed_refs",
        "label": {
            "de": "Ausführlich (mit Refs)",
            "en": "Detailed (with references)",
        },
        "description": {
            "de": "Abschnittsweise Zusammenfassung mit Zahlen, Paragraphen- "
            "und Quellenangaben.",
            "en": "Section-by-section summary keeping figures, clause numbers "
            "and references.",
        },
        "structure": (
            "A '## Summary' overview, then one '### ' subsection per major "
            "topic in the document, each with 5-15 sentences. Give every major "
            "topic in the content its own subsection; do not merge distinct "
            "topics together and do not leave one out. End with a "
            "'## Conclusion' section. Throughout, cite the source's own anchors "
            "inline and verbatim: clause and section numbers, "
            "figure/table/appendix identifiers, key quantities with units, and "
            "references to other documents or standards — e.g. "
            "\"gemäß § 29 Abs. 2 ...\", \"Abbildung 4 zeigt ...\", "
            "\"nach DIN 25457\". Cite only identifiers that appear in the "
            "content; never invent or guess one."
        ),
    },
    {
        "id": "bullets",
        "label": {"de": "Stichpunkte", "en": "Bullet key-points"},
        "description": {
            "de": "Einfache Liste der wichtigsten Erkenntnisse.",
            "en": "Flat list of the most important takeaways.",
        },
        "structure": (
            "Only a Markdown bullet list of 6-20 key takeaways. "
            "No headings, no prose paragraphs."
        ),
    },
    {
        "id": "action_items",
        "label": {"de": "Maßnahmen", "en": "Action items"},
        "description": {
            "de": "Entscheidungen und nächste Schritte als Aufgaben.",
            "en": "Decisions and next steps extracted as tasks.",
        },
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
