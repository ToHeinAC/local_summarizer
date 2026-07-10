import pytest
from streamlit.testing.v1 import AppTest

from src import app, i18n

APP_FILE = "src/app.py"

FAKE_MODELS = [
    {
        "id": "standard",
        "tag": "gemma4:e4b",
        "label": {"de": "Standard", "en": "Standard"},
        "note": {"de": "ausgewogen", "en": "balanced"},
        "speed": 2,
        "quality": 2,
        "installed": True,
    }
]


GAST_PW = "gast-test-pw"


@pytest.fixture
def anon(monkeypatch, tmp_path):
    """The app, run offline and signed out, with an isolated user store."""
    monkeypatch.setattr("src.models.annotate_availability", lambda host: FAKE_MODELS)
    monkeypatch.setattr("src.auth.DATA_ROOT", tmp_path)
    monkeypatch.setenv("SEED_PW_HEIN", "hein-test-pw")
    monkeypatch.setenv("SEED_PW_GAST", GAST_PW)
    return AppTest.from_file(APP_FILE).run()


@pytest.fixture
def at(anon):
    """The app, signed in as the default user."""
    anon.session_state["user"] = "T. Hein"
    return anon.run()


@pytest.fixture
def at_en(at):
    """The app, signed in, switched to English."""
    at.session_state["ui_lang"] = "en"
    return at.run()


def _sign_in(anon, username, password):
    anon.text_input[0].set_value(username)
    anon.text_input[1].set_value(password)
    return next(b for b in anon.button if b.label == "Anmelden").click().run()


def test_signed_out_app_shows_only_the_login_form(anon):
    assert not anon.tabs
    assert [i.label for i in anon.text_input] == ["Benutzername", "Passwort"]


def test_valid_credentials_sign_in(anon):
    at = _sign_in(anon, "Gast", GAST_PW)
    assert at.session_state["user"] == "Gast"
    assert [t.label for t in at.tabs] == ["1 · Umwandeln", "2 · Zusammenfassen"]


def test_invalid_credentials_are_rejected(anon):
    at = _sign_in(anon, "Gast", "wrong")
    assert "user" not in at.session_state
    assert at.error[0].value == "Benutzername oder Passwort ist ungültig."


def test_logout_clears_the_session(at):
    at.session_state["markdown"] = "# Hi"
    at.run()
    next(b for b in at.button if b.label == "Abmelden").click().run()
    assert "user" not in at.session_state
    assert "markdown" not in at.session_state
    assert not at.tabs


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
    assert [t.label for t in at.tabs] == ["1 · Umwandeln", "2 · Zusammenfassen"]


def test_sidebar_selects_only_a_model(at):
    """Language and template moved into the summarize tab."""
    labels = [s.label for s in at.sidebar.selectbox]
    assert labels == ["Modell"]


def test_summarize_tab_offers_language_and_template(at):
    labels = [s.label for s in at.selectbox]
    assert "Sprache der Zusammenfassung" in labels
    assert "Vorlage" in labels


def test_summary_source_defaults_to_upload_when_step1_is_empty(at):
    """With no converted Markdown yet, step 2 falls back to its own .md upload."""
    assert at.radio[0].value == i18n.t("source_upload", "de")


def test_summary_source_hints_when_step1_is_chosen_but_empty(at):
    at.radio[0].set_value(i18n.t("source_step1", "de")).run()
    assert at.info[0].value.startswith("Wandeln Sie zuerst in Schritt 1")


def test_summary_source_defaults_to_step1_markdown(at):
    at.session_state["markdown"] = "# Hi"
    at.run()
    assert at.radio[0].value == i18n.t("source_step1", "de")
    assert not at.info


def test_summarize_disabled_without_a_source(at):
    button = next(b for b in at.button if b.label == "Zusammenfassen")
    assert button.disabled


def test_summarize_enabled_with_step1_markdown(at):
    at.session_state["markdown"] = "# Hi"
    at.run()
    button = next(b for b in at.button if b.label == "Zusammenfassen")
    assert not button.disabled


def test_convert_button_disabled_without_upload(at):
    button = next(b for b in at.button if b.label == "In Markdown umwandeln")
    assert button.disabled


def test_step1_offers_a_markdown_download(at):
    at.session_state["markdown"] = "# Hi"
    at.run()
    assert any(d.label == ".md herunterladen" for d in at.download_button)


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
    next(b for b in at.button if b.label == "Zusammenfassen").click().run()

    assert calls["text"] == "# Source doc"
    assert "data" not in calls and "filename" not in calls
    assert at.session_state["summary"] == "## Overview\nDone."
    assert {d.label for d in at.download_button} >= {
        ".md herunterladen",
        ".docx herunterladen",
        ".pdf herunterladen",
    }


# --- GUI language toggle ----------------------------------------------------


def test_gui_language_defaults_to_german(at):
    assert at.session_state["ui_lang"] == "de"
    assert next(b for b in at.sidebar.button if b.key == "lang_btn").label == "🌐 English"


def test_toggle_button_switches_the_gui_to_english(at):
    at = next(b for b in at.sidebar.button if b.key == "lang_btn").click().run()
    assert at.session_state["ui_lang"] == "en"
    assert [t.label for t in at.tabs] == ["1 · Convert", "2 · Summarize"]
    assert next(b for b in at.sidebar.button if b.key == "lang_btn").label == "🌐 Deutsch"


def test_english_gui_translates_every_surface(at_en):
    assert [s.label for s in at_en.sidebar.selectbox] == ["Model"]
    assert {"Summary language", "Template"} <= {s.label for s in at_en.selectbox}
    assert any(b.label == "Summarize" for b in at_en.button)
    assert any(b.label == "Convert to Markdown" for b in at_en.button)
    assert any(b.label == "Exit app" for b in at_en.button)
    assert at_en.radio[0].value == i18n.t("source_upload", "en")


def test_toggle_survives_logout(at_en):
    """A shared machine keeps the chosen language, but drops the user's data."""
    at_en.session_state["markdown"] = "# Hi"
    at_en.run()
    at_en = next(b for b in at_en.button if b.label == "Logout").click().run()
    assert "user" not in at_en.session_state
    assert "markdown" not in at_en.session_state
    assert at_en.session_state["ui_lang"] == "en"
    assert at_en.text_input[0].label == "Username"


def test_summarize_passes_the_gui_language_to_the_agent(at_en, monkeypatch):
    """Progress labels are built in the agent layer, so it needs the GUI language."""
    calls = {}
    monkeypatch.setattr("src.agent.run", lambda **kw: calls.update(kw) or "# ok")
    at_en.session_state["markdown"] = "# Source doc"
    at_en.run()
    next(b for b in at_en.button if b.label == "Summarize").click().run()
    assert calls["ui_lang"] == "en"


def test_every_summary_language_has_a_name_in_both_guis():
    """format_func indexes LANGUAGE_NAMES directly, so a gap is a KeyError."""
    assert set(i18n.LANGUAGE_NAMES) == set(app.LANGUAGE_LABELS)
    for names in i18n.LANGUAGE_NAMES.values():
        assert set(names) == set(i18n.LANGUAGES)
