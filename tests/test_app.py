import pytest
from streamlit.testing.v1 import AppTest

from src import app

APP_FILE = "src/app.py"

FAKE_MODELS = [
    {
        "id": "standard",
        "tag": "gemma4:e4b",
        "label": "Standard",
        "note": "balanced",
        "speed": 2,
        "quality": 2,
        "installed": True,
    }
]


@pytest.fixture
def at(monkeypatch):
    """The app, run offline: no Ollama query for model availability."""
    monkeypatch.setattr("src.models.annotate_availability", lambda host: FAKE_MODELS)
    return AppTest.from_file(APP_FILE).run()


def test_stars():
    assert app._stars(3) == "★★★"
    assert app._stars(1) == "★☆☆"


def test_accepted_formats():
    assert app.ACCEPTED == ["pdf", "docx", "txt", "md"]


def test_config_loaded():
    assert app.CFG.app_port == 8530


def test_theme_css_available_to_ui():
    assert "<style>" in app.theme.build_css()


def test_two_tabs(at):
    assert [t.label for t in at.tabs] == ["1 · Convert", "2 · Summarize"]


def test_sidebar_selects_only_a_model(at):
    """Language and template moved into the summarize tab."""
    labels = [s.label for s in at.sidebar.selectbox]
    assert labels == ["Model"]


def test_summarize_tab_offers_language_and_template(at):
    labels = [s.label for s in at.selectbox]
    assert "Summary language" in labels
    assert "Template" in labels


def test_summary_source_defaults_to_upload_when_step1_is_empty(at):
    """With no converted Markdown yet, step 2 falls back to its own .md upload."""
    assert at.radio[0].value == app.SOURCE_UPLOAD


def test_summary_source_hints_when_step1_is_chosen_but_empty(at):
    at.radio[0].set_value(app.SOURCE_STEP1).run()
    assert at.info[0].value.startswith("Convert a document in step 1 first")


def test_summary_source_defaults_to_step1_markdown(at):
    at.session_state["markdown"] = "# Hi"
    at.run()
    assert at.radio[0].value == app.SOURCE_STEP1
    assert not at.info


def test_summarize_disabled_without_a_source(at):
    button = next(b for b in at.button if b.label == "Summarize")
    assert button.disabled


def test_summarize_enabled_with_step1_markdown(at):
    at.session_state["markdown"] = "# Hi"
    at.run()
    button = next(b for b in at.button if b.label == "Summarize")
    assert not button.disabled


def test_convert_button_disabled_without_upload(at):
    button = next(b for b in at.button if b.label == "Convert to Markdown")
    assert button.disabled


def test_step1_offers_a_markdown_download(at):
    at.session_state["markdown"] = "# Hi"
    at.run()
    assert any(d.label == "Download .md" for d in at.download_button)


def test_summarize_runs_on_markdown_without_reconverting(at, monkeypatch):
    """Step 2 summarizes text directly; it must never re-run file conversion."""
    calls = {}

    def fake_run(**kwargs):
        calls.update(kwargs)
        return "## Overview\nDone."

    monkeypatch.setattr("src.agent.run", fake_run)
    at.session_state["markdown"] = "# Source doc"
    at.session_state["stem"] = "report"
    at.run()
    next(b for b in at.button if b.label == "Summarize").click().run()

    assert calls["text"] == "# Source doc"
    assert "data" not in calls and "filename" not in calls
    assert at.session_state["summary"] == "## Overview\nDone."
    assert {d.label for d in at.download_button} >= {
        "Download .md",
        "Download .docx",
        "Download .pdf",
    }
