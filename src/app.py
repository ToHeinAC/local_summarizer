"""Streamlit UI for the local summarizer. No LangChain in this module.

All user-facing strings are German. Sign-in is required; the two-step workflow
follows, one tab each:

1. Convert — upload a document, turn it into Markdown, download the ``.md``.
2. Summarize — reuse step 1's Markdown (default) or upload your own ``.md``,
   choose language and template, summarize, download the result.

Run: uv run streamlit run src/app.py --server.port 8530
"""

from __future__ import annotations

import os
import signal

import streamlit as st

from src import agent, auth, export, extract, theme
from src.config import load_config
from src.models import DEFAULT_MODEL_ID, annotate_availability
from src.prompts import LANGUAGE_LABELS
from src.templates import DEFAULT_TEMPLATE_ID, list_templates

CFG = load_config()
ACCEPTED = ["pdf", "docx", "txt", "md"]
APP_TITLE = "KI-Zusammenfassung"
SOURCE_STEP1 = "Markdown aus Schritt 1"
SOURCE_UPLOAD = ".md-Datei hochladen"

# German display names for the language codes. Kept apart from
# prompts.LANGUAGE_LABELS, whose English names go into the finalize prompt.
LANGUAGE_UI_LABELS = {
    "auto": "Automatisch (Sprache des Dokuments)",
    "en": "Englisch",
    "de": "Deutsch",
    "fr": "Französisch",
    "es": "Spanisch",
    "it": "Italienisch",
    "pt": "Portugiesisch",
    "nl": "Niederländisch",
}


def _stars(n: int) -> str:
    return "★" * n + "☆" * (3 - n)


def _login_gate() -> None:
    """Show the sign-in form and stop the script until a user is signed in."""
    if st.session_state.get("user"):
        return

    _left, mid, _right = st.columns([1, 1.4, 1])
    with mid:
        st.markdown(f"## 📝 {APP_TITLE}")
        st.caption("Zum Fortfahren anmelden")
        with st.form("login_form"):
            username = st.text_input("Benutzername")
            password = st.text_input("Passwort", type="password")
            submitted = st.form_submit_button(
                "Anmelden", type="primary", use_container_width=True
            )
        if submitted:
            if auth.verify(username, password):
                st.session_state["user"] = username
                st.rerun()
            else:
                st.error("Benutzername oder Passwort ist ungültig.")
    st.stop()


def _sidebar() -> dict:
    st.sidebar.markdown(f"## 📝 {APP_TITLE}")
    st.sidebar.markdown("---")

    st.sidebar.caption("MODELL")
    models = annotate_availability(CFG.ollama_host)
    ids = [m["id"] for m in models]
    model_id = st.sidebar.selectbox(
        "Modell",
        ids,
        index=ids.index(DEFAULT_MODEL_ID),
        format_func=lambda i: next(m["label"] for m in models if m["id"] == i),
        label_visibility="collapsed",
    )
    model = next(m for m in models if m["id"] == model_id)
    st.sidebar.caption(
        f"Geschwindigkeit {_stars(model['speed'])}  Qualität {_stars(model['quality'])}"
    )
    st.sidebar.caption(model["note"])
    if not model["installed"]:
        st.sidebar.warning(
            f"`{model['tag']}` ist nicht installiert. Ausführen: `ollama pull {model['tag']}`"
        )

    st.sidebar.markdown("---")
    st.sidebar.caption(f"Angemeldet als **{st.session_state['user']}**")
    exit_col, logout_col = st.sidebar.columns(2)
    if exit_col.button("App beenden", key="exit_btn"):
        st.sidebar.info("Wird beendet…")
        os.kill(os.getpid(), signal.SIGTERM)
    if logout_col.button("Abmelden", key="logout_btn"):
        st.session_state.clear()  # drop the signed-in user and their documents
        st.rerun()

    return {"model": model}


def _convert(uploaded) -> None:
    bar = st.progress(0.0, text="Konvertiere zu Markdown…")

    def on_progress(done: int, total: int, label: str) -> None:
        bar.progress(done / total if total else 1.0, text=label)

    try:
        markdown = extract.to_markdown(
            uploaded.name,
            uploaded.getvalue(),
            ocr_model=CFG.ocr_model,
            rewrite_model=CFG.rewrite_model,
            dpi=CFG.pdf_dpi,
            host=CFG.ollama_host,
            on_progress=on_progress,
        )
    except Exception as exc:  # surface any conversion/OCR failure to the user
        bar.empty()
        st.error(f"Konvertierung fehlgeschlagen: {exc}")
        return

    bar.empty()
    if not markdown.strip():
        st.error("Im Dokument wurde kein extrahierbarer Text gefunden.")
        return
    st.session_state["markdown"] = markdown
    st.session_state["stem"] = os.path.splitext(uploaded.name)[0]
    st.session_state.pop("summary", None)


def _tab_convert() -> None:
    st.caption(
        "Dokumente werden zuerst in Markdown umgewandelt; "
        "gescannte PDF-Seiten werden lokal per OCR gelesen."
    )
    uploaded = st.file_uploader("Dokument hochladen", type=ACCEPTED)

    if st.button("In Markdown umwandeln", type="primary", disabled=uploaded is None):
        _convert(uploaded)

    markdown = st.session_state.get("markdown")
    if not markdown:
        return
    stem = st.session_state.get("stem", "dokument")
    st.markdown("---")
    st.subheader("Markdown")
    with st.container(border=True, height=400):
        st.markdown(markdown)
    st.download_button(
        ".md herunterladen",
        data=markdown.encode("utf-8"),
        file_name=f"{stem}.md",
        mime="text/markdown",
    )


def _summary_source() -> tuple[str | None, str]:
    """Return the Markdown to summarize and its filename stem."""
    has_step1 = bool(st.session_state.get("markdown"))
    source = st.radio(
        "Quelle",
        [SOURCE_STEP1, SOURCE_UPLOAD],
        index=0 if has_step1 else 1,
        horizontal=True,
        label_visibility="collapsed",
    )
    if source == SOURCE_STEP1:
        if not has_step1:
            st.info(
                "Wandeln Sie zuerst in Schritt 1 ein Dokument um, "
                "oder laden Sie hier eine `.md`-Datei hoch."
            )
            return None, "dokument"
        return st.session_state["markdown"], st.session_state.get("stem", "dokument")

    uploaded = st.file_uploader("Markdown-Datei hochladen", type=["md"])
    if uploaded is None:
        return None, "dokument"
    return (
        uploaded.getvalue().decode("utf-8", errors="replace"),
        os.path.splitext(uploaded.name)[0],
    )


def _summary_options() -> dict:
    left, right = st.columns(2)

    left.caption("SPRACHE")
    langs = list(LANGUAGE_LABELS)
    language = left.selectbox(
        "Sprache der Zusammenfassung",
        langs,
        index=langs.index(CFG.default_language) if CFG.default_language in langs else 0,
        format_func=lambda c: LANGUAGE_UI_LABELS[c],
        label_visibility="collapsed",
    )

    right.caption("VORLAGE")
    templates = list_templates()
    tpl_ids = [t["id"] for t in templates]
    template_id = right.selectbox(
        "Vorlage",
        tpl_ids,
        index=tpl_ids.index(DEFAULT_TEMPLATE_ID),
        format_func=lambda i: next(t["label"] for t in templates if t["id"] == i),
        label_visibility="collapsed",
    )
    right.caption(next(t["description"] for t in templates if t["id"] == template_id))

    return {"language": language, "template_id": template_id}


def _summarize(markdown: str, opts: dict, model: dict) -> None:
    bar = st.progress(0.0, text="Vorbereitung…")

    def on_progress(fraction: float, label: str) -> None:
        bar.progress(min(fraction, 1.0), text=label)

    try:
        summary = agent.run(
            text=markdown,
            template_id=opts["template_id"],
            model_id=model["id"],
            target_language=opts["language"],
            host=CFG.ollama_host,
            on_progress=on_progress,
        )
    except Exception as exc:  # surface any LLM failure to the user
        bar.empty()
        st.error(f"Zusammenfassung fehlgeschlagen: {exc}")
        return

    bar.empty()
    st.session_state["summary"] = summary


def _downloads(summary: str, stem: str) -> None:
    cols = st.columns(3)
    for col, fmt in zip(cols, ("md", "docx", "pdf")):
        mime, exporter = export.EXPORTERS[fmt]
        col.download_button(
            f".{fmt} herunterladen",
            data=exporter(summary),
            file_name=f"{stem}_zusammenfassung.{fmt}",
            mime=mime,
            use_container_width=True,
        )


def _tab_summarize(model: dict) -> None:
    markdown, stem = _summary_source()
    opts = _summary_options()

    disabled = markdown is None or not model["installed"]
    if st.button("Zusammenfassen", type="primary", disabled=disabled):
        _summarize(markdown, opts, model)

    if summary := st.session_state.get("summary"):
        st.markdown("---")
        st.subheader("Zusammenfassung")
        with st.container(border=True):
            st.markdown(summary)
        _downloads(summary, stem)


def main() -> None:
    st.set_page_config(
        page_title=APP_TITLE,
        page_icon="📝",
        layout="wide",
        initial_sidebar_state="expanded",
    )
    st.markdown(theme.build_css(), unsafe_allow_html=True)
    try:
        auth.ensure_seeded()
    except RuntimeError as exc:  # no seed passwords configured
        st.error(str(exc))
        st.stop()
    _login_gate()
    opts = _sidebar()

    st.title(APP_TITLE)
    convert_tab, summarize_tab = st.tabs(["1 · Umwandeln", "2 · Zusammenfassen"])
    with convert_tab:
        _tab_convert()
    with summarize_tab:
        _tab_summarize(opts["model"])


if __name__ == "__main__":
    main()
