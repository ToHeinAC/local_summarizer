"""LangGraph summarization agent: ingest -> chunk -> map -> reduce -> finalize.

LangChain/LangGraph are permitted in this module. Progress is reported through
an ``on_progress(fraction, label)`` callback passed via the run config, keeping
Streamlit out of the agent layer.
"""

from __future__ import annotations

from typing import Callable, Optional, TypedDict

from langgraph.graph import END, StateGraph

from src.extract import to_markdown
from src.i18n import DEFAULT_LANG, t
from src.language import detect_language
from src.models import get_model
from src.prompts import FINALIZE_PROMPT, LANGUAGE_LABELS, MAP_PROMPT, REDUCE_PROMPT
from src.templates import get_template
from src.tools import make_llm, run_prompt

CHUNK_SIZE = 6000
CHUNK_OVERLAP = 200
REDUCE_BATCH = 8  # partial summaries combined per hierarchical reduce step
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
    host: Optional[str]
    ocr_model: str
    rewrite_model: str
    pdf_dpi: int
    chunks: list[str]
    chunk_summaries: list[str]
    summary: str


def split_text(text: str, size: int = CHUNK_SIZE, overlap: int = CHUNK_OVERLAP) -> list[str]:
    """Split ``text`` into overlapping character-bounded chunks."""
    if len(text) <= size:
        return [text]
    chunks: list[str] = []
    start = 0
    step = max(1, size - overlap)
    while start < len(text):
        chunks.append(text[start : start + size])
        start += step
    return chunks


def _progress(config, fraction: float, label: str) -> None:
    fn = (config or {}).get("configurable", {}).get("on_progress")
    if fn:
        fn(fraction, label)


def _llm(state: SummaryState):
    return make_llm(state["model_tag"], state.get("host"))


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
        )
    if not text.strip():
        raise ValueError(t("no_text", lang))
    _progress(config, INGEST_SHARE, t("read_document", lang))
    return {"text": text, "source_language": detect_language(text)}


def _chunk(state: SummaryState, config) -> dict:
    chunks = split_text(state["text"])
    _progress(config, 0.42, t("split", _lang(state), count=len(chunks)))
    return {"chunks": chunks}


def _map(state: SummaryState, config) -> dict:
    chunks = state["chunks"]
    if len(chunks) == 1:
        return {"chunk_summaries": chunks}
    llm = _llm(state)
    lang = _lang(state)
    summaries: list[str] = []
    for i, chunk in enumerate(chunks, start=1):
        summaries.append(run_prompt(llm, MAP_PROMPT.format(chunk=chunk)))
        label = t("map_section", lang, done=i, total=len(chunks))
        _progress(config, 0.42 + 0.38 * i / len(chunks), label)
    return {"chunk_summaries": summaries}


def _reduce(state: SummaryState, config) -> dict:
    summaries = state["chunk_summaries"]
    llm = _llm(state)
    _progress(config, 0.85, t("reducing", _lang(state)))
    while len(summaries) > 1:
        batched: list[str] = []
        for i in range(0, len(summaries), REDUCE_BATCH):
            group = summaries[i : i + REDUCE_BATCH]
            joined = "\n\n---\n\n".join(group)
            batched.append(run_prompt(llm, REDUCE_PROMPT.format(summaries=joined)))
        summaries = batched
    return {"chunk_summaries": summaries}


def _finalize(state: SummaryState, config) -> dict:
    target = state.get("target_language", "auto")
    code = state["source_language"] if target == "auto" else target
    language = LANGUAGE_LABELS.get(code, code)
    template = get_template(state["template_id"])["structure"]
    content = state["chunk_summaries"][0]
    _progress(config, 0.90, t("finalizing", _lang(state)))
    summary = run_prompt(
        _llm(state),
        FINALIZE_PROMPT.format(language=language, template=template, content=content),
    )
    _progress(config, 1.0, t("done", _lang(state)))
    return {"summary": summary}


def _needs_reduce(state: SummaryState) -> str:
    return "reduce" if len(state["chunk_summaries"]) > 1 else "finalize"


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
    rewrite_model: str = "gemma4:e4b",
    pdf_dpi: int = 150,
    on_progress: Optional[ProgressFn] = None,
    ui_lang: str = DEFAULT_LANG,
) -> str:
    """Summarize a document and return Markdown.

    Provide either ``text`` or (``filename`` and ``data``). Files are converted
    to Markdown first; scanned PDF pages are OCR'd with ``ocr_model``.
    ``ui_lang`` is the GUI language of the progress labels; the summary's own
    language is ``target_language``.
    """
    state: SummaryState = {
        "ui_lang": ui_lang,
        "filename": filename,
        "data": data,
        "text": text,
        "target_language": target_language,
        "template_id": template_id,
        "model_tag": get_model(model_id)["tag"],
        "host": host,
        "ocr_model": ocr_model,
        "rewrite_model": rewrite_model,
        "pdf_dpi": pdf_dpi,
    }
    config = {"configurable": {"on_progress": on_progress}}
    result = build_graph().invoke(state, config=config)
    return result["summary"]
