"""UI string catalogue. Plain python, no LangChain.

German is the default GUI language; English is the alternative. Only strings a
*user* reads live here — strings the *LLM* reads (``prompts.py``, a template's
``structure``) stay English regardless of the GUI language.

``t(key, lang, **fmt)`` looks a string up and applies ``str.format``. Registry
labels (``models.py``, ``templates.py``) carry their own ``{"de", "en"}`` dicts
next to the data they describe; use ``pick()`` to read them.
"""

from __future__ import annotations

DEFAULT_LANG = "de"

# GUI languages, in toggle order. Values are the button labels.
LANGUAGES = {"de": "Deutsch", "en": "English"}

# Display names for the *summary* language codes (prompts.LANGUAGE_LABELS keys).
LANGUAGE_NAMES: dict[str, dict[str, str]] = {
    "auto": {"de": "Automatisch (Sprache des Dokuments)", "en": "Auto (document's language)"},
    "en": {"de": "Englisch", "en": "English"},
    "de": {"de": "Deutsch", "en": "German"},
    "fr": {"de": "Französisch", "en": "French"},
    "es": {"de": "Spanisch", "en": "Spanish"},
    "it": {"de": "Italienisch", "en": "Italian"},
    "pt": {"de": "Portugiesisch", "en": "Portuguese"},
    "nl": {"de": "Niederländisch", "en": "Dutch"},
}

STRINGS: dict[str, dict[str, str]] = {
    # --- shell -------------------------------------------------------------
    "app_title": {"de": "KI-Zusammenfassung", "en": "AI Summarizer"},
    # --- sign-in -----------------------------------------------------------
    "sign_in_hint": {"de": "Zum Fortfahren anmelden", "en": "Sign in to continue"},
    "username": {"de": "Benutzername", "en": "Username"},
    "password": {"de": "Passwort", "en": "Password"},
    "sign_in": {"de": "Anmelden", "en": "Sign in"},
    "bad_credentials": {
        "de": "Benutzername oder Passwort ist ungültig.",
        "en": "Invalid username or password.",
    },
    "seed_missing": {
        "de": "Keine Start-Passwörter gefunden. Bitte {vars} in .env setzen (siehe .env.example).",
        "en": "No seed passwords found. Set {vars} in .env (see .env.example).",
    },
    # --- sidebar -----------------------------------------------------------
    "model_caption": {"de": "MODELL", "en": "MODEL"},
    "model_label": {"de": "Modell", "en": "Model"},
    "speed_quality": {
        "de": "Geschwindigkeit {speed}  Qualität {quality}",
        "en": "Speed {speed}  Quality {quality}",
    },
    "not_installed": {
        "de": "`{tag}` ist nicht installiert. Ausführen: `ollama pull {tag}`",
        "en": "`{tag}` is not installed. Run: `ollama pull {tag}`",
    },
    "signed_in_as": {"de": "Angemeldet als **{user}**", "en": "Signed in as **{user}**"},
    "logout": {"de": "Abmelden", "en": "Logout"},
    "advanced_options": {"de": "Erweiterte Optionen", "en": "Advanced options"},
    "clear_vram": {"de": "CUDA-Speicher leeren", "en": "Clear CUDA memory"},
    "vram_cleared": {
        "de": "{n} Modell(e) aus dem VRAM entladen.",
        "en": "Unloaded {n} model(s) from VRAM.",
    },
    "vram_empty": {"de": "Keine Modelle geladen.", "en": "No models were loaded."},
    # --- main panel: upload & summarize ------------------------------------
    "intro_hint": {
        "de": "Modell, Sprache und Vorlage wählen, ein Dokument hochladen und zusammenfassen.",
        "en": "Choose model, language and template, upload a document, and summarize.",
    },
    "upload_document": {"de": "Dokument hochladen", "en": "Upload a document"},
    "precision_caption": {"de": "PRÄZISION", "en": "PRECISION"},
    "precision_label": {"de": "Präzision", "en": "Precision"},
    "fast_option": {"de": "Schnellmodus (wörtlich)", "en": "Fast mode (verbatim)"},
    "precise_option": {"de": "Genaues Markdown (LLM)", "en": "Precise Markdown (LLM)"},
    "llm_format_help": {
        "de": (
            "Formatiert jede Textseite vor dem Zusammenfassen per LLM neu "
            "(Überschriften, Listen, Tabellen), ohne den Wortlaut zu ändern. "
            "Ein LLM-Aufruf pro Seite — deutlich langsamer. Standardmäßig aus: "
            "der Text wird verbatim gelesen."
        ),
        "en": (
            "Reformats each text page with the LLM before summarizing "
            "(headings, lists, tables) without changing the wording. "
            "One LLM call per page — much slower. Off by default: the text is "
            "read verbatim."
        ),
    },
    "download_format": {"de": ".{fmt} herunterladen", "en": "Download .{fmt}"},
    "default_stem": {"de": "dokument", "en": "document"},
    "language_caption": {"de": "SPRACHE", "en": "LANGUAGE"},
    "selection_hint": {"de": "Auswahl", "en": "Selection"},
    "language_label": {"de": "Sprache der Zusammenfassung", "en": "Summary language"},
    "template_caption": {"de": "VORLAGE", "en": "TEMPLATE"},
    "template_label": {"de": "Vorlage", "en": "Template"},
    "summarize_button": {"de": "Zusammenfassen", "en": "Summarize"},
    "summary_heading": {"de": "Zusammenfassung", "en": "Summary"},
    "summary_suffix": {"de": "zusammenfassung", "en": "summary"},
    "summarize_failed": {
        "de": "Zusammenfassung fehlgeschlagen: {error}",
        "en": "Summarization failed: {error}",
    },
    # --- progress & errors (agent.py, md_convert.py, extract.py) -----------
    "preparing": {"de": "Vorbereitung…", "en": "Preparing…"},
    "converting": {"de": "Konvertiere zu Markdown…", "en": "Converting to Markdown…"},
    "convert_start": {"de": "Konvertiere zu Markdown", "en": "Converting to Markdown"},
    "page": {"de": "Seite {done}/{total} ({kind})", "en": "Page {done}/{total} ({kind})"},
    "converted": {"de": "In Markdown umgewandelt", "en": "Converted to Markdown"},
    "read_document": {"de": "Dokument gelesen", "en": "Read document"},
    "split": {"de": "In {count} Abschnitt(e) geteilt", "en": "Split into {count} section(s)"},
    "map_section": {
        "de": "Fasse Abschnitt {done}/{total} zusammen",
        "en": "Summarizing section {done}/{total}",
    },
    "reducing": {
        "de": "Führe Abschnitts-Zusammenfassungen zusammen",
        "en": "Combining section summaries",
    },
    "finalizing": {"de": "Schreibe finale Zusammenfassung", "en": "Writing final summary"},
    "done": {"de": "Fertig", "en": "Done"},
    "no_text": {
        "de": "Im Dokument wurde kein extrahierbarer Text gefunden.",
        "en": "No extractable text found in the document.",
    },
    "unsupported_file": {
        "de": "Nicht unterstützter Dateityp '{ext}'. Unterstützt: {supported}",
        "en": "Unsupported file type '{ext}'. Supported: {supported}",
    },
}


def t(key: str, lang: str = DEFAULT_LANG, **fmt: object) -> str:
    """Return the ``lang`` variant of ``key``, formatted with ``fmt``."""
    text = STRINGS[key][lang if lang in LANGUAGES else DEFAULT_LANG]
    return text.format(**fmt) if fmt else text


def pick(field: dict[str, str], lang: str = DEFAULT_LANG) -> str:
    """Return the ``lang`` variant of a registry field like ``model["label"]``."""
    return field[lang if lang in LANGUAGES else DEFAULT_LANG]
