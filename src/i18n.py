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
        "de": (
            "Modell, Präzission, Sprache und Vorlage wählen, ein Dokument "
            "hochladen und zusammenfassen."
        ),
        "en": (
            "Choose model, precision, language and template, upload a document, "
            "and summarize."
        ),
    },
    "upload_document": {"de": "Dokument hochladen", "en": "Upload a document"},
    "precision_caption": {"de": "PRÄZISION PDF", "en": "PRECISION PDF"},
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
    "download_converted": {
        "de": "Erzeugtes Markdown herunterladen (.md)",
        "en": "Download generated Markdown (.md)",
    },
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
    # --- portfolio ---------------------------------------------------------
    "nav_caption": {"de": "BEREICH", "en": "SECTION"},
    "mode_summarize": {"de": "📝 Zusammenfassung", "en": "📝 Summary"},
    "mode_portfolio": {"de": "📈 Portfolio", "en": "📈 Portfolio"},
    "portfolio_title": {"de": "Portfolio", "en": "Portfolio"},
    "portfolio_intro": {
        "de": (
            "Ein Portfolio als CSV hochladen (Ticker, Stückzahl, Kaufpreis), Kurse "
            "abrufen und die Positionen im Blick behalten. Nach dem 100-Bagger-Prinzip: "
            "Qualität halten und nicht zu früh verkaufen."
        ),
        "en": (
            "Upload a portfolio as CSV (ticker, quantity, buy price), fetch prices "
            "and keep an eye on the positions. Following the 100-bagger principle: "
            "hold quality and don't sell too soon."
        ),
    },
    "portfolio_template": {"de": "Vorlage (CSV) herunterladen", "en": "Download template (CSV)"},
    "portfolio_upload": {"de": "Portfolio hochladen (CSV)", "en": "Upload portfolio (CSV)"},
    "portfolio_parse_error": {
        "de": "CSV konnte nicht gelesen werden: {error}",
        "en": "Could not read the CSV: {error}",
    },
    "portfolio_upload_hint": {
        "de": "Lade eine CSV hoch, um zu beginnen. Spalten: ticker, quantity, buy_price.",
        "en": "Upload a CSV to begin. Columns: ticker, quantity, buy_price.",
    },
    "update_prices": {"de": "Kurse aktualisieren", "en": "Update prices"},
    "prices_offline": {
        "de": "Keine Live-Kurse verfügbar (offline). Kurse unten manuell eingeben.",
        "en": "No live prices available (offline). Enter prices manually below.",
    },
    "prices_partial": {
        "de": "Für {n} Position(en) fehlt ein Kurs — bitte manuell eingeben.",
        "en": "{n} position(s) have no price — enter them manually.",
    },
    "manual_prices_caption": {"de": "MANUELLE KURSE", "en": "MANUAL PRICES"},
    "manual_price_label": {"de": "{ticker} Kurs", "en": "{ticker} price"},
    "total_value": {"de": "Wert", "en": "Value"},
    "total_cost": {"de": "Einstand", "en": "Cost"},
    "total_gain": {"de": "Gewinn/Verlust", "en": "Gain/Loss"},
    "col_ticker": {"de": "Ticker", "en": "Ticker"},
    "col_qty": {"de": "Stück", "en": "Qty"},
    "col_buy": {"de": "Kaufpreis", "en": "Buy"},
    "col_price": {"de": "Kurs", "en": "Price"},
    "col_value": {"de": "Wert", "en": "Value"},
    "col_gain_pct": {"de": "G/V %", "en": "Gain %"},
    "col_multiple": {"de": "Vielfaches", "en": "Multiple"},
    "col_weight": {"de": "Gewicht", "en": "Weight"},
    "col_reco": {"de": "Empfehlung", "en": "Recommendation"},
    "reco_hold": {"de": "🟢 Halten", "en": "🟢 Hold"},
    "reco_add": {"de": "🔵 Aufstocken", "en": "🔵 Add"},
    "reco_trim": {"de": "🟠 Reduzieren", "en": "🟠 Trim"},
    "reco_review": {"de": "🔴 Prüfen", "en": "🔴 Review"},
    "reco_legend": {
        "de": (
            "🟢 Halten (Standard) · 🔵 Aufstocken bei Rücksetzer · "
            "🟠 Reduzieren bei Klumpenrisiko · 🔴 Prüfen (These gebrochen). "
            "Keine Anlageberatung."
        ),
        "en": (
            "🟢 Hold (default) · 🔵 Add on a dip · 🟠 Trim on concentration risk · "
            "🔴 Review (thesis broken). Not investment advice."
        ),
    },
    "download_snapshot": {"de": "Portfolio (CSV) herunterladen", "en": "Download portfolio (CSV)"},
    "portfolio_positions": {"de": "Positionen", "en": "Positions"},
}


def t(key: str, lang: str = DEFAULT_LANG, **fmt: object) -> str:
    """Return the ``lang`` variant of ``key``, formatted with ``fmt``."""
    text = STRINGS[key][lang if lang in LANGUAGES else DEFAULT_LANG]
    return text.format(**fmt) if fmt else text


def pick(field: dict[str, str], lang: str = DEFAULT_LANG) -> str:
    """Return the ``lang`` variant of a registry field like ``model["label"]``."""
    return field[lang if lang in LANGUAGES else DEFAULT_LANG]
