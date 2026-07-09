"""LangGraph summarization agent: ingest -> chunk -> map -> reduce -> finalize.

LangChain/LangGraph are permitted in this module. Progress is reported through
an ``on_progress(fraction, label)`` callback passed via the run config, keeping
Streamlit out of the agent layer.
"""

from __future__ import annotations

from typing import Callable, Optional, TypedDict

from langgraph.graph import END, StateGraph

from src.extract import extract_text
from src.language import detect_language
from src.models import get_model
from src.prompts import FINALIZE_PROMPT, LANGUAGE_LABELS, MAP_PROMPT, REDUCE_PROMPT
from src.templates import get_template
from src.tools import make_llm, run_prompt

CHUNK_SIZE = 6000
CHUNK_OVERLAP = 200
REDUCE_BATCH = 8  # partial summaries combined per hierarchical reduce step

ProgressFn = Callable[[float, str], None]


class SummaryState(TypedDict, total=False):
    filename: str
    data: bytes
    text: str
    source_language: str
    target_language: str
    template_id: str
    model_tag: str
    host: Optional[str]
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


def _ingest(state: SummaryState, config) -> dict:
    text = state.get("text") or extract_text(state["filename"], state["data"])
    if not text.strip():
        raise ValueError("No extractable text found in the document.")
    _progress(config, 0.05, "Reading document")
    return {"text": text, "source_language": detect_language(text)}


def _chunk(state: SummaryState, config) -> dict:
    chunks = split_text(state["text"])
    _progress(config, 0.10, f"Split into {len(chunks)} section(s)")
    return {"chunks": chunks}


def _map(state: SummaryState, config) -> dict:
    chunks = state["chunks"]
    if len(chunks) == 1:
        return {"chunk_summaries": chunks}
    llm = _llm(state)
    summaries: list[str] = []
    for i, chunk in enumerate(chunks, start=1):
        summaries.append(run_prompt(llm, MAP_PROMPT.format(chunk=chunk)))
        _progress(config, 0.10 + 0.65 * i / len(chunks), f"Summarizing section {i}/{len(chunks)}")
    return {"chunk_summaries": summaries}


def _reduce(state: SummaryState, config) -> dict:
    summaries = state["chunk_summaries"]
    llm = _llm(state)
    _progress(config, 0.80, "Combining section summaries")
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
    _progress(config, 0.90, "Writing final summary")
    summary = run_prompt(
        _llm(state),
        FINALIZE_PROMPT.format(language=language, template=template, content=content),
    )
    _progress(config, 1.0, "Done")
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
    on_progress: Optional[ProgressFn] = None,
) -> str:
    """Summarize a document and return Markdown.

    Provide either ``text`` or (``filename`` and ``data``).
    """
    state: SummaryState = {
        "filename": filename,
        "data": data,
        "text": text,
        "target_language": target_language,
        "template_id": template_id,
        "model_tag": get_model(model_id)["tag"],
        "host": host,
    }
    config = {"configurable": {"on_progress": on_progress}}
    result = build_graph().invoke(state, config=config)
    return result["summary"]
