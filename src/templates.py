"""Summary template registry. Plain python, no LangChain.

``label`` and ``description`` are per-GUI-language dicts (read with
``i18n.pick``). Each template's ``structure`` string stays English: it is
injected into FINALIZE_PROMPT to steer the summary's format and information
density.
"""

from __future__ import annotations

# Page targets are given to the LLM as word counts (one A4 page of prose is
# roughly 500 words). Heading names are English here; FINALIZE_PROMPT has the
# model translate them into the summary language.
TEMPLATES: list[dict] = [
    {
        "id": "executive",
        "label": {"de": "Executive Summary (½ Seite)", "en": "Executive summary (½ page)"},
        "description": {
            "de": "Fließtext für Entscheider: Ziel, entscheidende Ergebnisse, Schlussfolgerung.",
            "en": "Prose for decision makers: objective, decisive results, conclusion.",
        },
        "structure": (
            "An executive summary of 250-300 words (half an A4 page) for decision "
            "makers: three paragraphs of continuous prose, no headings, no lists. "
            "Paragraph 1: what the document is, who prepared it for whom, and its "
            "objective. Paragraph 2: the decisive results with their key figures. "
            "Paragraph 3: the conclusions and the recommended next steps."
        ),
    },
    {
        "id": "bullets",
        "label": {"de": "Stichpunkte (1 Seite)", "en": "Bullet points (1 page)"},
        "description": {
            "de": "Zielstellung, Methodik und Ergebnisse als Stichpunktliste.",
            "en": "Objective, methodology and results as bullet points.",
        },
        "structure": (
            "A bullet-point summary of 450-550 words (one A4 page) with exactly "
            "these three sections:\n"
            "'## Objective' - 2-3 bullets: what the document sets out to do and why.\n"
            "'## Methodology' - 3-5 bullets: approach, data, measurements, models "
            "or sources used.\n"
            "'## Results' - 10-16 bullets: the main findings and conclusions, each "
            "with its key figures and units.\n"
            "Every bullet is one or two complete sentences. No prose outside the "
            "bullets. Fill the page: stay within 450-550 words, not fewer."
        ),
    },
    {
        "id": "detailed",
        "label": {
            "de": "Ausführlich mit Referenzen (2 Seiten)",
            "en": "Detailed with references (2 pages)",
        },
        "description": {
            "de": "Zielstellung, Methodik, Ergebnisse je Thema, Schlussfolgerungen "
            "und die wesentlichen zitierten Dokumente.",
            "en": "Objective, methodology, results per topic, conclusions and the "
            "key documents cited.",
        },
        "structure": (
            "A detailed summary of 1000-1200 words (two A4 pages) with these sections:\n"
            "'## Objective' - one paragraph: purpose, scope, author and client, context.\n"
            "'## Methodology' - one paragraph: approach, data, measurements, models "
            "and assumptions.\n"
            "'## Results' - one '### ' subsection per major topic of the document, "
            "each with 4-8 sentences of prose; give every major topic its own "
            "subsection and leave none out.\n"
            "'## Conclusions' - one paragraph with the conclusions and recommendations.\n"
            "'## References' - a bullet list of the 5-12 most important documents, "
            "standards and regulations the document builds on (not its whole "
            "bibliography), each with its identifier "
            "exactly as the document writes it and a few words on what it is used "
            "for; leave out a reference the content gives no detail on.\n"
            "Throughout, cite the source's own anchors inline and verbatim: section "
            "and clause numbers, figure/table/appendix identifiers, key quantities "
            "with units and citation keys, the way the document itself writes "
            "them (a § number, 'Abbildung 3-2', a bracketed key). Cite only "
            "identifiers that appear in the content; never invent or guess one."
        ),
    },
    {
        "id": "action_items",
        "label": {"de": "Maßnahmen (1 Seite)", "en": "Action items (1 page)"},
        "description": {
            "de": "Kurz Ziel und Methodik, dann Erkenntnisse, Schlussfolgerungen und Maßnahmen.",
            "en": "Brief objective and method, then findings, conclusions and measures.",
        },
        "structure": (
            "An action-oriented summary of 450-550 words (one A4 page) with these "
            "sections:\n"
            "'## Objective' - one or two sentences.\n"
            "'## Methodology' - one or two sentences.\n"
            "'## Key Findings' - 4-8 bullets with the essential findings and their "
            "key figures.\n"
            "'## Conclusions' - 3-6 bullets: what the document concludes from the findings.\n"
            "'## Measures' - 4-10 bullets: the measures, recommendations and next "
            "steps that follow from the document, each as one complete, grammatical "
            "sentence that does not address the reader, naming the responsible "
            "party, deadline or target value where the document states one. List "
            "only measures the document supports; do not invent new ones.\n"
            "Fill the page: stay within 450-550 words, not fewer."
        ),
    },
]

DEFAULT_TEMPLATE_ID = "bullets"


def list_templates() -> list[dict]:
    """Return all registered templates."""
    return TEMPLATES


def get_template(template_id: str) -> dict:
    """Return the template entry for ``template_id``; raise KeyError if unknown."""
    for template in TEMPLATES:
        if template["id"] == template_id:
            return template
    raise KeyError(f"Unknown template id: {template_id}")
