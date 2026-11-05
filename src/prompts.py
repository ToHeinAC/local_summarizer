"""All LLM prompt strings live here as named module-level constants.

Never embed prompt strings inline in other modules. Placeholders use
``str.format`` style ({name}); callers fill them before invoking the LLM.
"""

# Shared by MAP_PROMPT and REDUCE_PROMPT: finalize only ever sees their output,
# so an identifier dropped here can never be cited in the summary.
_ANCHORS = """Copy these verbatim wherever they appear — they let a reader find the passage
in the source:
1. quantities with their units;
2. section and clause identifiers (§ and Art. numbers, numbered headings);
3. figure, table and appendix identifiers (Abbildung, Table, Anhang, ...);
4. citations of other documents: standards and norms (DIN, ISO, VDI numbers),
   laws, reports and citation keys exactly as the source writes them;
5. names of people and organisations, and dates.
Reproduce each one exactly as written: do not renumber, round, translate, or
abbreviate. Keep every fact in the same bullet as the identifier it belongs to.
Only use identifiers that appear in the text itself — never take one from
these instructions."""

# Shared by every note-taking prompt and FINALIZE_PROMPT: the exporters render
# only headings, bullets and paragraphs, and small models drift into LaTeX.
_PLAIN = """Write units, isotopes and formulas as plain text (Ra-226, 650 nSv/h, BaSO4,
Kd in ml/g) — no LaTeX, no $ signs, no bold, no tables."""

# Only for documents too long for one prompt: gives every map call the global
# context (purpose, structure) a single part cannot show on its own.
BRIEF_PROMPT = """Below are the opening pages of a long document (title page, table of
contents, abstract or introduction). Write a short overview of the whole
document, at most 200 words, in the same language as the document:
- title, author or issuing organisation, client, date (if stated)
- type of document (report, study, regulation, ...) and its stated objective
- the main chapters or parts, in order
Use only what is written there. """ + _PLAIN + """ No preamble.

OPENING PAGES:
{head}
"""

MAP_PROMPT = """You are taking notes on part {part} of {total} of a long document. The final
summary will be written from these notes alone — its writer never sees the
source — so whatever you leave out is lost.

DOCUMENT OVERVIEW:
{brief}

{focus}Write the notes in the same language as the part below. Use these headings,
in this order, and leave out any heading this part has nothing for:
### Objective and scope
### Method and data
### Results
### Conclusions
### Recommendations and measures
### Referenced documents

Under each heading write concise, complete bullet points, at most 800 words in
total. Weight them by what matters for the document's overall objective (see
the overview): main results, key figures, conclusions and recommendations in
full; routine detail briefly or not at all. Never repeat a bullet.
Under "Referenced documents" list only what the text builds on — documents cited
for its method, data, limits or conclusions. If this part is a bibliography,
keep at most the 15 entries the document relies on most, not the whole list.

""" + _ANCHORS + """
""" + _PLAIN + """

Do not add information that is not present. No preamble.

PART {part} OF {total}:
{chunk}
"""

REDUCE_PROMPT = """You are merging notes taken on consecutive parts of one document into a single
set of notes. Keep the same headings, write in the same language as the notes,
merge overlapping points, remove repetition, and keep every distinct fact,
figure, conclusion, recommendation and reference. Do not add new information.

Every identifier, quantity and reference in the notes must appear in your merged
notes, unchanged: section and clause numbers (§ and Art. numbers),
figure/table/appendix identifiers, quantities with their units, references to
other documents and standards, names and dates. Merging two mentions of the same
identifier is fine; dropping one is not.
""" + _PLAIN + """

No preamble.

NOTES:
{summaries}
"""

FINALIZE_PROMPT = """You are writing the final summary of a document.

Write everything in {language}, including the headings: give each heading named
below only in {language}, without the English name in brackets.
Follow this structure and length exactly:
{template}

{overview}{focus}Base the summary only on the content below. Do not invent facts, figures or
references.
Formatting: Markdown headings, "-" bullets and paragraphs only.
""" + _PLAIN + """
Never repeat a sentence, bullet or section.
Output only the summary: no preamble, no closing remarks.

CONTENT ({content_kind}):
{content}
"""

# Fills FINALIZE_PROMPT's {overview} / {content_kind} slots. Multi-part only:
# without the merge rule gemma copied the per-part note layout and restarted
# the whole structure for every part (StrlSchV: "Zielsetzung" three times).
FINALIZE_OVERVIEW = """DOCUMENT OVERVIEW:
{brief}

The content is notes on {total} consecutive parts, each under the same note
headings. Merge them by topic into one summary of the whole document: every
section of the structure above appears exactly once, in that order, with its
Markdown heading (## or ###). The note headings and part labels themselves do
not appear.

"""
# Fill MAP_PROMPT's / FINALIZE_PROMPT's {focus} slot when the user set a focus
# (a question to answer or a direction to weight towards); "" otherwise. Map
# must see it too: finalize only reads the notes, so a detail on the focus that
# the notes dropped as routine can never reach the summary.
MAP_FOCUS = """READER'S FOCUS (set by the user):
{focus}

Besides the usual notes, record in full everything this part says about that
focus (statements, figures, conditions, gaps), even if it looks routine, under
the most fitting heading. Do not stretch the text to fit the focus.

"""
FINALIZE_FOCUS = """READER'S FOCUS (set by the user: a question to answer, or a direction to
weight the summary towards):
{focus}

Orient the whole summary on this focus: content related to it gets priority and
detail, the rest stays brief. Begin with a short section, at most 120 words,
under a "## " Markdown heading that names the focus in {language} (never the
English word "Focus"). It states whether the document addresses the
focus, how and where (cite section, figure or table identifiers as written), and
what it concludes about it. If the document does not address it, say so plainly
instead of guessing. Then follow the structure above.

"""
NOTES_PART_HEADER = "=== NOTES ON PART {part} OF {total} ==="
CONTENT_FULL = "the full document"
CONTENT_NOTES = "notes taken on consecutive parts of the document"

# --- Markdown conversion (src/md_convert.py) --------------------------------

OCR_SYSTEM_PROMPT = """You are a precise document transcription assistant.
Your sole task is to convert the content of the provided document image
into well-structured Markdown, preserving the original structure faithfully.

Rules:
- Reproduce ALL text exactly as it appears — do not paraphrase or summarize.
- Use Markdown headings (#, ##, ###) that match the visual hierarchy.
- Render tables as proper Markdown tables (|col|col|).
- Preserve bullet/numbered lists exactly.
- Wrap code blocks in triple backticks with a language hint if detectable.
- For mathematical expressions, use LaTeX: $...$ inline, $$...$$ block.
- For figures/diagrams with no extractable text, write: [Figure: <brief description>]
- Do NOT add explanatory text, preamble, or commentary.
- Output ONLY the Markdown content — nothing else."""

OCR_USER_PROMPT = "Convert this document page to Markdown."

# deepseek-ocr requires a short, punctuated prompt on its own line after the image.
# The <|grounding|> token activates layout-aware OCR; omitting it degrades structure.
OCR_DEEPSEEK_PROMPT = "<|grounding|>Convert the document to markdown."

MD_REWRITE_PROMPT = """You are reformatting extracted PDF text as Markdown.

CRITICAL RULE: Do NOT change, paraphrase, summarize, translate, or reorder
any wording. Reproduce every word exactly. You may only:
- Add Markdown headings (#, ##, ###) to match visual hierarchy.
- Convert lists to Markdown bullet/numbered lists.
- Convert tabular text to Markdown tables when clearly tabular.
- Wrap code in fenced blocks.
- Use $...$ / $$...$$ for math if present.

Do not add commentary, preamble, or explanations. Output only Markdown.

Text to reformat:
"""

# Human-readable labels for finalize; "auto" resolves to the detected language.
LANGUAGE_LABELS = {
    "auto": "the document's main language",
    "en": "English",
    "de": "German",
    "fr": "French",
    "es": "Spanish",
    "it": "Italian",
    "pt": "Portuguese",
    "nl": "Dutch",
}
