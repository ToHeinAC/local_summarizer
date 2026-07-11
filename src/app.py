"""Streamlit UI for the local summarizer. No LangChain in this module.

The GUI language is German by default and toggles to English with the sidebar
button; every user-facing string comes from ``i18n``. Sign-in is required; the
two-step workflow follows, one tab each:

1. Convert — upload a document, turn it into Markdown, download the ``.md``.
2. Summarize — reuse step 1's Markdown (default) or upload your own ``.md``,
   choose language and template, summarize, download the result.

Run: uv run streamlit run src/app.py --server.port 8530
"""

from __future__ import annotations

import os
import signal

import streamlit as st

from src import agent, auth, export, extract, ollama_client, theme
from src.config import load_config
from src.i18n import DEFAULT_LANG, LANGUAGE_NAMES, LANGUAGES, pick, t
from src.models import DEFAULT_MODEL_ID, annotate_availability
from src.prompts import LANGUAGE_LABELS
from src.templates import DEFAULT_TEMPLATE_ID, list_templates

CFG = load_config()
ACCEPTED = ["pdf", "docx", "txt", "md"]


def _stars(n: int) -> str:
    return "★" * n + "☆" * (3 - n)


def _ui_lang() -> str:
    """The GUI language for this run; survives reruns via the session state."""
    return st.session_state.setdefault("ui_lang", DEFAULT_LANG)


def _language_toggle(container) -> None:
    """A single button that switches the GUI to the other language."""
    current = _ui_lang()
    other = next(code for code in LANGUAGES if code != current)
    if container.button(f"🌐 {LANGUAGES[other]}", key="lang_btn"):
        st.session_state["ui_lang"] = other
        st.rerun()


def _login_gate() -> None:
    """Show the sign-in form and stop the script until a user is signed in."""
    if st.session_state.get("user"):
        return

    lang = _ui_lang()
    _left, mid, _right = st.columns([1, 1.4, 1])
    with mid:
        st.markdown(f"## 📝 {t('app_title', lang)}")
        st.caption(t("sign_in_hint", lang))
        with st.form("login_form"):
            username = st.text_input(t("username", lang))
            password = st.text_input(t("password", lang), type="password")
            submitted = st.form_submit_button(
                t("sign_in", lang), type="primary", use_container_width=True
            )
        if submitted:
            if auth.verify(username, password):
                st.session_state["user"] = username
                st.rerun()
            else:
                st.error(t("bad_credentials", lang))
        _language_toggle(mid)
    st.stop()


def _sidebar(lang: str) -> dict:
    st.sidebar.markdown(f"## 📝 {t('app_title', lang)}")
    _language_toggle(st.sidebar)
    st.sidebar.markdown("---")

    st.sidebar.caption(t("model_caption", lang))
    models = annotate_availability(CFG.ollama_host)
    ids = [m["id"] for m in models]
    model_id = st.sidebar.selectbox(
        t("model_label", lang),
        ids,
        index=ids.index(DEFAULT_MODEL_ID),
        format_func=lambda i: pick(next(m["label"] for m in models if m["id"] == i), lang),
        label_visibility="collapsed",
    )
    model = next(m for m in models if m["id"] == model_id)
    st.sidebar.caption(
        t("speed_quality", lang, speed=_stars(model["speed"]), quality=_stars(model["quality"]))
    )
    st.sidebar.caption(pick(model["note"], lang))
    if not model["installed"]:
        st.sidebar.warning(t("not_installed", lang, tag=model["tag"]))

    with st.sidebar.expander(t("advanced_options", lang), expanded=False):
        if st.button(t("clear_vram", lang), key="clear_vram_btn"):
            unloaded = ollama_client.unload_all(CFG.ollama_host)
            if unloaded:
                st.success(t("vram_cleared", lang, n=len(unloaded)))
            else:
                st.info(t("vram_empty", lang))

    st.sidebar.markdown("---")
    st.sidebar.caption(t("signed_in_as", lang, user=st.session_state["user"]))
    exit_col, logout_col = st.sidebar.columns(2)
    if exit_col.button(t("exit_app", lang), key="exit_btn"):
        st.sidebar.info(t("shutting_down", lang))
        os.kill(os.getpid(), signal.SIGTERM)
    if logout_col.button(t("logout", lang), key="logout_btn"):
        lang = st.session_state.get("ui_lang", DEFAULT_LANG)
        st.session_state.clear()  # drop the signed-in user and their documents
        st.session_state["ui_lang"] = lang  # but keep the chosen GUI language
        st.rerun()

    return {"model": model}


def _convert(uploaded, lang: str) -> None:
    bar = st.progress(0.0, text=t("converting", lang))

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
            lang=lang,
        )
    except Exception as exc:  # surface any conversion/OCR failure to the user
        bar.empty()
        st.error(t("conversion_failed", lang, error=exc))
        return

    bar.empty()
    if not markdown.strip():
        st.error(t("no_text", lang))
        return
    st.session_state["markdown"] = markdown
    st.session_state["stem"] = os.path.splitext(uploaded.name)[0]
    st.session_state.pop("summary", None)


def _tab_convert(lang: str) -> None:
    st.caption(t("convert_hint", lang))
    uploaded = st.file_uploader(t("upload_document", lang), type=ACCEPTED)

    if st.button(t("convert_button", lang), type="primary", disabled=uploaded is None):
        _convert(uploaded, lang)

    markdown = st.session_state.get("markdown")
    if not markdown:
        return
    stem = st.session_state.get("stem", t("default_stem", lang))
    st.markdown("---")
    st.subheader("Markdown")
    with st.container(border=True, height=400):
        st.markdown(markdown)
    st.download_button(
        t("download_format", lang, fmt="md"),
        data=markdown.encode("utf-8"),
        file_name=f"{stem}.md",
        mime="text/markdown",
    )


def _summary_source(lang: str) -> tuple[str | None, str]:
    """Return the Markdown to summarize and its filename stem."""
    has_step1 = bool(st.session_state.get("markdown"))
    step1, upload = t("source_step1", lang), t("source_upload", lang)
    source = st.radio(
        t("source_label", lang),
        [step1, upload],
        index=0 if has_step1 else 1,
        horizontal=True,
        label_visibility="collapsed",
    )
    fallback_stem = t("default_stem", lang)
    if source == step1:
        if not has_step1:
            st.info(t("step1_hint", lang))
            return None, fallback_stem
        return st.session_state["markdown"], st.session_state.get("stem", fallback_stem)

    uploaded = st.file_uploader(t("upload_markdown", lang), type=["md"])
    if uploaded is None:
        return None, fallback_stem
    return (
        uploaded.getvalue().decode("utf-8", errors="replace"),
        os.path.splitext(uploaded.name)[0],
    )


def _summary_options(lang: str) -> dict:
    left, right = st.columns(2)

    left.caption(t("language_caption", lang))
    langs = list(LANGUAGE_LABELS)
    language = left.selectbox(
        t("language_label", lang),
        langs,
        index=langs.index(CFG.default_language) if CFG.default_language in langs else 0,
        format_func=lambda c: pick(LANGUAGE_NAMES[c], lang),
        label_visibility="collapsed",
    )

    right.caption(t("template_caption", lang))
    templates = list_templates()
    tpl_ids = [x["id"] for x in templates]
    template_id = right.selectbox(
        t("template_label", lang),
        tpl_ids,
        index=tpl_ids.index(DEFAULT_TEMPLATE_ID),
        format_func=lambda i: pick(next(x["label"] for x in templates if x["id"] == i), lang),
        label_visibility="collapsed",
    )
    right.caption(pick(next(x["description"] for x in templates if x["id"] == template_id), lang))

    return {"language": language, "template_id": template_id}


def _summarize(markdown: str, opts: dict, model: dict, lang: str) -> None:
    bar = st.progress(0.0, text=t("preparing", lang))

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
            ui_lang=lang,
        )
    except Exception as exc:  # surface any LLM failure to the user
        bar.empty()
        st.error(t("summarize_failed", lang, error=exc))
        return

    bar.empty()
    st.session_state["summary"] = summary


def _downloads(summary: str, stem: str, lang: str) -> None:
    cols = st.columns(3)
    suffix = t("summary_suffix", lang)
    for col, fmt in zip(cols, ("md", "docx", "pdf")):
        mime, exporter = export.EXPORTERS[fmt]
        col.download_button(
            t("download_format", lang, fmt=fmt),
            data=exporter(summary),
            file_name=f"{stem}_{suffix}.{fmt}",
            mime=mime,
            use_container_width=True,
        )


def _tab_summarize(model: dict, lang: str) -> None:
    markdown, stem = _summary_source(lang)
    opts = _summary_options(lang)

    disabled = markdown is None or not model["installed"]
    if st.button(t("summarize_button", lang), type="primary", disabled=disabled):
        _summarize(markdown, opts, model, lang)

    if summary := st.session_state.get("summary"):
        st.markdown("---")
        st.subheader(t("summary_heading", lang))
        with st.container(border=True):
            st.markdown(summary)
        _downloads(summary, stem, lang)


def main() -> None:
    lang = _ui_lang()
    st.set_page_config(
        page_title=t("app_title", lang),
        page_icon="📝",
        layout="wide",
        initial_sidebar_state="expanded",
    )
    st.markdown(theme.build_css(), unsafe_allow_html=True)
    try:
        auth.ensure_seeded()
    except RuntimeError:  # no seed passwords configured
        st.error(t("seed_missing", lang, vars=" / ".join(auth.SEED_USERS.values())))
        st.stop()
    _login_gate()
    opts = _sidebar(lang)

    st.title(t("app_title", lang))
    convert_tab, summarize_tab = st.tabs([t("tab_convert", lang), t("tab_summarize", lang)])
    with convert_tab:
        _tab_convert(lang)
    with summarize_tab:
        _tab_summarize(opts["model"], lang)


if __name__ == "__main__":
    main()
