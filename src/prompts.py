"""All LLM prompt strings live here as named module-level constants.

Never embed prompt strings inline in other modules. Placeholders use
``str.format`` style ({name}); callers fill them before invoking the LLM.
"""

MAP_PROMPT = """You are summarizing one section of a longer document.
Write a faithful, self-contained summary of the section below.
Keep every key fact, name, number, and conclusion. Do not add information
that is not present. Output plain prose, no preamble.

SECTION:
{chunk}
"""

REDUCE_PROMPT = """You are combining several partial summaries of one document
into a single coherent summary. Merge overlapping points, remove repetition,
and preserve every distinct key fact and conclusion. Do not add new information.
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
