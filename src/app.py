"""Streamlit UI for the local summarizer. No LangChain in this module.

Run: uv run streamlit run src/app.py --server.port 8506
"""

from __future__ import annotations

import os
import signal

import streamlit as st

from src import agent, export, theme
from src.config import load_config
from src.models import DEFAULT_MODEL_ID, annotate_availability
from src.prompts import LANGUAGE_LABELS
from src.templates import DEFAULT_TEMPLATE_ID, list_templates

CFG = load_config()
ACCEPTED = ["pdf", "docx", "txt", "md"]


def _stars(n: int) -> str:
    return "★" * n + "☆" * (3 - n)


def _sidebar() -> dict:
    st.sidebar.markdown("## 📝 Summarizer")
    st.sidebar.markdown("---")

    st.sidebar.caption("LANGUAGE")
    langs = list(LANGUAGE_LABELS)
    language = st.sidebar.selectbox(
        "Summary language",
        langs,
        index=langs.index(CFG.default_language) if CFG.default_language in langs else 0,
        format_func=lambda c: LANGUAGE_LABELS[c].capitalize(),
        label_visibility="collapsed",
    )

    st.sidebar.caption("TEMPLATE")
    templates = list_templates()
    tpl_ids = [t["id"] for t in templates]
    template_id = st.sidebar.selectbox(
        "Template",
        tpl_ids,
        index=tpl_ids.index(DEFAULT_TEMPLATE_ID),
        format_func=lambda i: next(t["label"] for t in templates if t["id"] == i),
        label_visibility="collapsed",
    )
    st.sidebar.caption(next(t["description"] for t in templates if t["id"] == template_id))

    st.sidebar.caption("MODEL")
    models = annotate_availability(CFG.ollama_host)
    ids = [m["id"] for m in models]
    model_id = st.sidebar.selectbox(
        "Model",
        ids,
        index=ids.index(DEFAULT_MODEL_ID),
        format_func=lambda i: next(m["label"] for m in models if m["id"] == i),
        label_visibility="collapsed",
    )
    model = next(m for m in models if m["id"] == model_id)
    st.sidebar.caption(f"Speed {_stars(model['speed'])}  Quality {_stars(model['quality'])}")
    st.sidebar.caption(model["note"])
    if not model["installed"]:
        st.sidebar.warning(f"`{model['tag']}` is not installed. Run: `ollama pull {model['tag']}`")

    st.sidebar.markdown("---")
    if st.sidebar.button("Exit app", key="exit_btn", use_container_width=True):
        st.sidebar.info("Shutting down…")
        os.kill(os.getpid(), signal.SIGTERM)

    return {"language": language, "template_id": template_id, "model": model}


def _summarize(uploaded, opts: dict) -> None:
    bar = st.progress(0.0, text="Preparing…")

    def on_progress(fraction: float, label: str) -> None:
        bar.progress(min(fraction, 1.0), text=label)

    try:
        summary = agent.run(
            filename=uploaded.name,
            data=uploaded.getvalue(),
            template_id=opts["template_id"],
            model_id=opts["model"]["id"],
            target_language=opts["language"],
            host=CFG.ollama_host,
            ocr_model=CFG.ocr_model,
            rewrite_model=CFG.rewrite_model,
            pdf_dpi=CFG.pdf_dpi,
            on_progress=on_progress,
        )
    except Exception as exc:  # surface any ingest/LLM failure to the user
        bar.empty()
        st.error(f"Summarization failed: {exc}")
        return

    bar.empty()
    st.session_state["summary"] = summary
    st.session_state["stem"] = os.path.splitext(uploaded.name)[0]


def _downloads(summary: str, stem: str) -> None:
    cols = st.columns(3)
    for col, fmt in zip(cols, ("md", "docx", "pdf")):
        mime, exporter = export.EXPORTERS[fmt]
        col.download_button(
            f"Download .{fmt}",
            data=exporter(summary),
            file_name=f"{stem}_summary.{fmt}",
            mime=mime,
            use_container_width=True,
        )


def main() -> None:
    st.set_page_config(
        page_title="Local Summarizer",
        page_icon="📝",
        layout="wide",
        initial_sidebar_state="expanded",
    )
    st.markdown(theme.build_css(), unsafe_allow_html=True)
    opts = _sidebar()

    st.title("Document Summarizer")
    st.caption("Documents are converted to Markdown first; scanned PDF pages are OCR'd locally.")
    uploaded = st.file_uploader("Upload a document", type=ACCEPTED)

    disabled = uploaded is None or not opts["model"]["installed"]
    if st.button("Summarize", type="primary", disabled=disabled):
        _summarize(uploaded, opts)

    if summary := st.session_state.get("summary"):
        st.markdown("---")
        st.subheader("Summary")
        with st.container(border=True):
            st.markdown(summary)
        _downloads(summary, st.session_state.get("stem", "document"))


if __name__ == "__main__":
    main()
