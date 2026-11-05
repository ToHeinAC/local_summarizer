"""LangGraph summarization agent: ingest -> chunk -> map -> reduce -> finalize.

LangChain/LangGraph are permitted in this module. Progress is reported through
an ``on_progress(fraction, label)`` callback passed via the run config, keeping
Streamlit out of the agent layer.
"""

from __future__ import annotations

import math
from typing import Callable, Optional, TypedDict

from langgraph.graph import END, StateGraph

from src.extract import to_markdown
from src.i18n import DEFAULT_LANG, t
from src.language import detect_language
from src.models import get_model, num_ctx
from src.ollama_client import unload
from src.prompts import (
    BRIEF_PROMPT,
    CONTENT_FULL,
    CONTENT_NOTES,
    FINALIZE_FOCUS,
    FINALIZE_OVERVIEW,
    FINALIZE_PROMPT,
    LANGUAGE_LABELS,
    MAP_FOCUS,
    MAP_PROMPT,
    NOTES_PART_HEADER,
    REDUCE_PROMPT,
)
from src.templates import get_template
from src.tools import NUM_PREDICT, make_llm, run_prompt

# Source text per prompt is sized from the model's window (models.NUM_CTX), not
# a fixed character count. MAX_INPUT_TOKENS caps it for summary quality: one
# answer holds only a few thousand tokens of notes, so bigger parts lose more
# (StrlSchV: 113 of 200 §§ reach the notes with 32k parts, 49 with 120k).
# RESERVED_TOKENS covers the prompt, the overview and the answer.
MAX_INPUT_TOKENS = 32768
RESERVED_TOKENS = NUM_PREDICT + 2048
# Measured 3.0-3.5 chars/token on German reports (~4 on English prose); the
# quality cap uses the typical rate. The hard window uses the worst case:
# Ollama silently drops the start of a prompt that exceeds num_ctx.
CHARS_PER_TOKEN = 3.3
MIN_CHARS_PER_TOKEN = 2.5
CHUNK_OVERLAP = 1000
BRIEF_CHARS = 20000  # title pages + table of contents + introduction
REDUCE_BATCH = 8  # note sets combined per hierarchical reduce step
INGEST_SHARE = 0.40  # progress budget for the file -> Markdown conversion

ProgressFn = Callable[[float, str], None]


class SummaryState(TypedDict, total=False):
    ui_lang: str  # GUI language of the progress labels, not the summary language
    filename: str
    data: bytes
    text: str
    source_language: str
    target_language: str
    template_id: str
    model_tag: str
    map_model_tag: str  # cheaper model for map/reduce; hybrid models only
    host: Optional[str]
    ocr_model: str
    rewrite_model: str
    pdf_dpi: int
    fast: bool
    focus: str  # user's question or direction for the summary; "" for none
    chunks: list[str]
    brief: str  # whole-document overview; only for multi-part documents
    chunk_summaries: list[str]
    summary: str


def input_chars(tag: str) -> int:
    """Characters of source text one prompt to ``tag`` may safely carry."""
    never_truncated = (num_ctx(tag) - RESERVED_TOKENS) * MIN_CHARS_PER_TOKEN
    return int(min(never_truncated, MAX_INPUT_TOKENS * CHARS_PER_TOKEN))


def split_text(text: str, size: int, overlap: int = CHUNK_OVERLAP) -> list[str]:
    """Split ``text`` into the fewest balanced chunks of at most ``size`` chars.

    Chunks overlap by ``overlap`` chars and end on a line break where one is
    near, so no sentence is cut mid-word and no tiny tail chunk is left over.
    """
    if len(text) <= size:
        return [text]
    overlap = min(overlap, size // 4)  # guarantees every chunk advances
    count = math.ceil(len(text) / (size - overlap))
    target = math.ceil(len(text) / count)
    chunks: list[str] = []
    start = 0
    while True:
        end = start + target + overlap
        if end >= len(text):
            chunks.append(text[start:])
            return chunks
        cut = text.rfind("\n", start + target // 2, end)
        end = cut + 1 if cut != -1 else end
        chunks.append(text[start:end])
        start = end - overlap


def _progress(config, fraction: float, label: str) -> None:
    fn = (config or {}).get("configurable", {}).get("on_progress")
    if fn:
        fn(fraction, label)


def _llm(state: SummaryState):
    return make_llm(state["model_tag"], state.get("host"))


def _map_tag(state: SummaryState) -> str:
    """Tag for the per-chunk passes: the hybrid's small model, else the main one."""
    return state.get("map_model_tag") or state["model_tag"]


def _map_llm(state: SummaryState):
    return make_llm(_map_tag(state), state.get("host"))


def _lang(state: SummaryState) -> str:
    return state.get("ui_lang", DEFAULT_LANG)


def _ingest(state: SummaryState, config) -> dict:
    lang = _lang(state)
    text = state.get("text")
    if not text:
        # Seed at 0.0: the first conversion callback also reports 0 pages done,
        # so anything higher here would make the progress bar run backwards.
        _progress(config, 0.0, t("convert_start", lang))

        def on_convert(done: int, total: int, label: str) -> None:
            fraction = INGEST_SHARE * done / total if total else INGEST_SHARE
            _progress(config, fraction, label)

        text = to_markdown(
            state["filename"],
            state["data"],
            ocr_model=state["ocr_model"],
            rewrite_model=state["rewrite_model"],
            dpi=state["pdf_dpi"],
            host=state.get("host"),
            on_progress=on_convert,
            lang=lang,
            fast=state.get("fast", False),
        )
    if not text.strip():
        raise ValueError(t("no_text", lang))
    _progress(config, INGEST_SHARE, t("read_document", lang))
    return {"text": text, "source_language": detect_language(text)}


def _chunk(state: SummaryState, config) -> dict:
    """One part if the whole text fits the final model, else balanced parts."""
    text = state["text"]
    if len(text) <= input_chars(state["model_tag"]):
        chunks = [text]
    else:
        chunks = split_text(text, input_chars(_map_tag(state)))
    _progress(config, 0.42, t("split", _lang(state), count=len(chunks)))
    return {"chunks": chunks}


def _map(state: SummaryState, config) -> dict:
    """Take structured notes on each part, all guided by one document overview."""
    chunks = state["chunks"]
    if len(chunks) == 1:
        return {"chunk_summaries": chunks, "brief": ""}
    llm = _map_llm(state)
    lang = _lang(state)
    _progress(config, 0.43, t("overview", lang))
    brief = run_prompt(llm, BRIEF_PROMPT.format(head=state["text"][:BRIEF_CHARS]))
    focus = MAP_FOCUS.format(focus=state["focus"]) if state.get("focus") else ""
    summaries: list[str] = []
    total = len(chunks)
    for i, chunk in enumerate(chunks, start=1):
        prompt = MAP_PROMPT.format(part=i, total=total, brief=brief, focus=focus, chunk=chunk)
        summaries.append(run_prompt(llm, prompt))
        _progress(config, 0.43 + 0.37 * i / total, t("map_section", lang, done=i, total=total))
    return {"chunk_summaries": summaries, "brief": brief}


def _join(summaries: list[str]) -> str:
    return "\n\n---\n\n".join(summaries)


def _reduce(state: SummaryState, config) -> dict:
    """Merge note sets hierarchically until they fit one finalize prompt."""
    summaries = state["chunk_summaries"]
    llm = _map_llm(state)
    budget = input_chars(state["model_tag"])
    _progress(config, 0.85, t("reducing", _lang(state)))
    while len(summaries) > 1 and len(_join(summaries)) > budget:
        summaries = [
            run_prompt(llm, REDUCE_PROMPT.format(summaries=_join(summaries[i : i + REDUCE_BATCH])))
            for i in range(0, len(summaries), REDUCE_BATCH)
        ]
    return {"chunk_summaries": summaries}


def _final_content(state: SummaryState) -> tuple[str, str, str]:
    """(overview, content kind, content) for FINALIZE_PROMPT."""
    notes = state["chunk_summaries"]
    if len(state["chunks"]) == 1:
        return "", CONTENT_FULL, notes[0]
    total = len(notes)
    content = "\n\n".join(
        f"{NOTES_PART_HEADER.format(part=i, total=total)}\n{n}"
        for i, n in enumerate(notes, start=1)
    )
    return FINALIZE_OVERVIEW.format(brief=state["brief"], total=total), CONTENT_NOTES, content


def _finalize(state: SummaryState, config) -> dict:
    target = state.get("target_language", "auto")
    code = state["source_language"] if target == "auto" else target
    _progress(config, 0.90, t("finalizing", _lang(state)))
    if state.get("map_model_tag") and len(state["chunks"]) > 1:
        unload(state["map_model_tag"], state.get("host"))  # free VRAM for the final model
    overview, kind, content = _final_content(state)
    language = LANGUAGE_LABELS.get(code, code)
    focus = state.get("focus")
    prompt = FINALIZE_PROMPT.format(
        language=language,
        template=get_template(state["template_id"])["structure"],
        overview=overview,
        focus=FINALIZE_FOCUS.format(focus=focus, language=language) if focus else "",
        content_kind=kind,
        content=content,
    )
    summary = run_prompt(_llm(state), prompt)
    _progress(config, 1.0, t("done", _lang(state)))
    return {"summary": summary}


def _needs_reduce(state: SummaryState) -> str:
    notes = state["chunk_summaries"]
    too_long = len(_join(notes)) > input_chars(state["model_tag"])
    return "reduce" if len(notes) > 1 and too_long else "finalize"


def build_graph():
    """Compile the summarization state graph."""
    graph = StateGraph(SummaryState)
    graph.add_node("ingest", _ingest)
    graph.add_node("chunk", _chunk)
    graph.add_node("map", _map)
    graph.add_node("reduce", _reduce)
    graph.add_node("finalize", _finalize)

    graph.set_entry_point("ingest")
    graph.add_edge("ingest", "chunk")
    graph.add_edge("chunk", "map")
    graph.add_conditional_edges("map", _needs_reduce, {"reduce": "reduce", "finalize": "finalize"})
    graph.add_edge("reduce", "finalize")
    graph.add_edge("finalize", END)
    return graph.compile()


def run(
    *,
    template_id: str,
    model_id: str,
    filename: str = "",
    data: bytes = b"",
    text: str = "",
    target_language: str = "auto",
    host: Optional[str] = None,
    ocr_model: str = "deepseek-ocr:3b",
    rewrite_model: str = "gemma3:4b",
    pdf_dpi: int = 150,
    fast: bool = False,
    on_progress: Optional[ProgressFn] = None,
    ui_lang: str = DEFAULT_LANG,
    return_markdown: bool = False,
    focus: str = "",
):
    """Summarize a document and return Markdown.

    Provide either ``text`` or (``filename`` and ``data``). Files are converted
    to Markdown first; scanned PDF pages are OCR'd with ``ocr_model``. ``fast``
    skips the per-page LLM rewrite for digital PDF pages (verbatim text layer).
    ``ui_lang`` is the GUI language of the progress labels; the summary's own
    language is ``target_language``. ``focus`` is an optional question or
    direction the summary is oriented on (map notes and finalize); blank = none.

    Returns the summary Markdown. With ``return_markdown=True`` returns a
    ``(summary, converted_markdown)`` tuple, where the second item is the text the
    document was converted to before summarizing (the LLM-rewritten Markdown when
    ``fast=False``).
    """
    model = get_model(model_id)
    state: SummaryState = {
        "ui_lang": ui_lang,
        "filename": filename,
        "data": data,
        "text": text,
        "target_language": target_language,
        "template_id": template_id,
        "model_tag": model["tag"],
        "map_model_tag": model.get("map_tag", ""),
        "host": host,
        "ocr_model": ocr_model,
        "rewrite_model": rewrite_model,
        "pdf_dpi": pdf_dpi,
        "fast": fast,
        "focus": focus.strip(),
    }
    config = {"configurable": {"on_progress": on_progress}}
    result = build_graph().invoke(state, config=config)
    if return_markdown:
        return result["summary"], result["text"]
    return result["summary"]
