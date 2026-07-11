"""Streamlit UI for the local summarizer. No LangChain in this module.

The GUI language is German by default and toggles to English with the sidebar
button; every user-facing string comes from ``i18n``. Sign-in is required.

Single-window workflow: pick a model (sidebar), choose the summary language and
template, upload a document, press **Zusammenfassen**. Conversion is plain text
(digital pages verbatim, scanned pages OCR'd) and feeds straight into the
summarizer, so one click produces the summary and its downloads — no separate
convert step and no intermediate Markdown.

Run: uv run streamlit run src/app.py --server.port 8530
"""

from __future__ import annotations

import os

import streamlit as st

from src import agent, auth, export, ollama_client, theme
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


def _sidebar(lang: str) -> None:
    st.sidebar.markdown(f"## 📝 {t('app_title', lang)}")
    st.sidebar.markdown("---")

    with st.sidebar.expander(t("advanced_options", lang), expanded=False):
        if st.button(t("clear_vram", lang), key="clear_vram_btn"):
            unloaded = ollama_client.unload_all(CFG.ollama_host)
            if unloaded:
                st.success(t("vram_cleared", lang, n=len(unloaded)))
            else:
                st.info(t("vram_empty", lang))

    st.sidebar.markdown("---")
    st.sidebar.caption(t("signed_in_as", lang, user=st.session_state["user"]))
    _language_toggle(st.sidebar)  # full-width, above logout
    # Logout only clears session state (no process kill), so the app process —
    # and any Cloudflare tunnel in front of it — stays alive for the next user.
    if st.sidebar.button(t("logout", lang), key="logout_btn"):
        lang = st.session_state.get("ui_lang", DEFAULT_LANG)
        st.session_state.clear()  # drop the signed-in user and their documents
        st.session_state["ui_lang"] = lang  # but keep the chosen GUI language
        st.rerun()


def _model_selector(container, lang: str) -> dict:
    """Render the model picker (with its speed/quality stars) into a container."""
    container.caption(t("model_caption", lang))
    models = annotate_availability(CFG.ollama_host)
    ids = [m["id"] for m in models]
    model_id = container.selectbox(
        t("model_label", lang),
        ids,
        index=ids.index(DEFAULT_MODEL_ID),
        format_func=lambda i: pick(next(m["label"] for m in models if m["id"] == i), lang),
        label_visibility="collapsed",
    )
    model = next(m for m in models if m["id"] == model_id)
    container.caption(
        t("speed_quality", lang, speed=_stars(model["speed"]), quality=_stars(model["quality"]))
    )
    if not model["installed"]:
        container.warning(t("not_installed", lang, tag=model["tag"]))
    return model


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
    left.caption(t("selection_hint", lang))

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


def _run(uploaded, opts: dict, model: dict, lang: str) -> None:
    """Convert the upload and summarize it in one pass."""
    bar = st.progress(0.0, text=t("preparing", lang))

    def on_progress(fraction: float, label: str) -> None:
        bar.progress(min(fraction, 1.0), text=label)

    precise = opts["llm_format"]
    try:
        result = agent.run(
            filename=uploaded.name,
            data=uploaded.getvalue(),
            template_id=opts["template_id"],
            model_id=model["id"],
            target_language=opts["language"],
            host=CFG.ollama_host,
            ocr_model=CFG.ocr_model,
            rewrite_model=CFG.rewrite_model,
            pdf_dpi=CFG.pdf_dpi,
            # fast=True reads text verbatim; the precise option flips it to the
            # per-page rewrite for nicer Markdown (one LLM call per page).
            fast=not precise,
            on_progress=on_progress,
            ui_lang=lang,
            # In precise mode also return the LLM-formatted document Markdown,
            # so the UI can offer it as a download alongside the summary.
            return_markdown=precise,
        )
    except Exception as exc:  # surface any conversion/LLM failure to the user
        bar.empty()
        st.error(t("summarize_failed", lang, error=exc))
        return

    bar.empty()
    summary, converted_md = result if precise else (result, None)
    st.session_state["summary"] = summary
    st.session_state["converted_md"] = converted_md
    st.session_state["stem"] = os.path.splitext(uploaded.name)[0]


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


def _main_panel(lang: str) -> None:
    st.caption(t("intro_hint", lang))

    # Quality parameters: model choice + the precision (LLM-Markdown) step.
    model_col, precision_col = st.columns(2)
    model = _model_selector(model_col, lang)
    precision_col.caption(t("precision_caption", lang))
    # False = fast (verbatim), True = LLM-rewritten Markdown.
    llm_format = precision_col.selectbox(
        t("precision_label", lang),
        [False, True],
        index=0,
        format_func=lambda v: t("precise_option" if v else "fast_option", lang),
        label_visibility="collapsed",
        help=t("llm_format_help", lang),
    )
    speed, quality = (1, 3) if llm_format else (3, 1)
    precision_col.caption(
        t("speed_quality", lang, speed=_stars(speed), quality=_stars(quality))
    )

    uploaded = st.file_uploader(t("upload_document", lang), type=ACCEPTED)

    opts = _summary_options(lang)
    opts["llm_format"] = llm_format

    disabled = uploaded is None or not model["installed"]
    if st.button(t("summarize_button", lang), type="primary", disabled=disabled):
        _run(uploaded, opts, model, lang)

    if summary := st.session_state.get("summary"):
        st.markdown("---")
        stem = st.session_state.get("stem", t("default_stem", lang))
        if converted_md := st.session_state.get("converted_md"):
            st.download_button(
                t("download_converted", lang),
                data=converted_md.encode("utf-8"),
                file_name=f"{stem}.md",
                mime="text/markdown",
                key="download_converted_btn",
            )
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
    _sidebar(lang)

    st.title(t("app_title", lang))
    _main_panel(lang)


if __name__ == "__main__":
    main()
