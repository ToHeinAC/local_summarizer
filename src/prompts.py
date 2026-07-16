"""All LLM prompt strings live here as named module-level constants.

Never embed prompt strings inline in other modules. Placeholders use
``str.format`` style ({name}); callers fill them before invoking the LLM.
"""

MAP_PROMPT = """You are summarizing one section of a longer document.
Write a faithful, self-contained summary of the section below.
Keep every key fact, name, number, and conclusion.

Copy the following verbatim wherever they appear — they are the anchors a reader
needs to find the passage in the source:
1. Quantities with their units (12,4 mg/kg, 3,2 Mio. EUR, 15 %).
2. Section and clause identifiers (§ 29 Abs. 2, Art. 5, Clause 4.1, 3.2.1).
3. Figure, table and appendix identifiers (Abbildung 4, Table 2, Anhang B).
4. References to other documents, standards and norms (DIN 25457, VDI 2263,
   "Gutachten vom 12.03.2024").
5. Names of people and organisations, and dates.

Reproduce each one exactly as written: do not renumber, round, translate, or
abbreviate. Keep every fact in the same sentence as the identifier it belongs to.
Do not add information that is not present. Output plain prose, no preamble.

SECTION:
{chunk}
"""

REDUCE_PROMPT = """You are combining several partial summaries of one document
into a single coherent summary. Merge overlapping points, remove repetition,
and preserve every distinct key fact and conclusion. Do not add new information.

Every identifier, quantity and reference that appears in the partial summaries
must appear in your combined summary, unchanged: section and clause numbers
(§ 29 Abs. 2, Art. 5), figure/table/appendix identifiers, quantities with their
units, references to other documents and standards, names and dates. Merging two
mentions of the same identifier is fine; dropping one is not.

Output plain prose, no preamble.

PARTIAL SUMMARIES:
{summaries}
"""

FINALIZE_PROMPT = """You are producing the final summary of a document.

Write the summary in this language: {language}.
Follow this structure and level of detail exactly:
{template}

Base the summary only on the content below. Do not invent facts.
Output valid Markdown, no preamble or closing remarks.

CONTENT:
{content}
"""

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
