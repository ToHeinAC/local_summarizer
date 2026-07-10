"""Forest theme: palette + injectable CSS. Plain python, no LangChain.

Ported from ToHeinAC/KB_BS_local-wiki-he (Apache-2.0) so both apps share a
look. Colors mirror ``.streamlit/config.toml``; the CSS below re-asserts them
because Streamlit's config alone does not reach every widget.
"""

from __future__ import annotations

FOREST = {
    "bg": "#f6f7f2",
    "sidebar_bg": "#eaf0ec",
    "widget_bg": "#ffffff",
    "text": "#1a1f1c",
    "text_muted": "#5a6b5e",
    "primary": "#234637",
    "border": "#d4dbd6",
    "hover": "rgba(35,70,55,0.10)",
}

_FONTS = (
    "https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600"
    "&family=Libre+Baskerville:ital,wght@0,400;0,700;1,400&display=swap"
)


def build_css(t: dict = FOREST) -> str:
    """Return the ``<style>`` block for the given palette."""
    return f"""
    <style>
    @import url('{_FONTS}');

    html, body {{
        font-family: 'Inter', system-ui, sans-serif;
        font-size: 15px;
    }}
    /* Catch ALL elements' color — overrides Streamlit's inline textColor from
       config.toml. Do NOT set font-family here: it breaks icon ligatures. */
    .stApp, .stApp * {{
        color: {t['text']} !important;
    }}
    [data-testid="stIconMaterial"],
    span.material-icons,
    span.material-icons-outlined,
    .material-symbols-rounded,
    .material-symbols-outlined,
    [class*="material-symbols"] {{
        font-family: 'Material Symbols Rounded', 'Material Icons' !important;
    }}

    .stApp {{ background-color: {t['bg']} !important; }}
    [data-testid="stSidebar"] {{ background-color: {t['sidebar_bg']} !important; }}
    [data-testid="block-container"],
    [data-testid="stVerticalBlock"],
    section.main > div {{
        background-color: {t['bg']} !important;
    }}

    h1, h2, h3 {{
        font-family: 'Libre Baskerville', Georgia, serif !important;
        font-weight: 700;
    }}
    h1 {{ font-size: 1.75rem; margin-bottom: 0.25rem; }}
    [data-testid="stSidebar"] h2 {{ white-space: nowrap; font-size: 1.25rem; }}

    .stSelectbox > div > div,
    .stSelectbox > div > div > div {{
        background-color: {t['widget_bg']} !important;
        color: {t['text']} !important;
        border-color: {t['border']} !important;
        border-radius: 6px !important;
    }}

    .stButton > button {{
        border-radius: 6px !important;
        font-weight: 500 !important;
        text-transform: none !important;
        font-size: 0.875rem !important;
        border: 1px solid {t['border']} !important;
        background-color: {t['widget_bg']} !important;
        color: {t['text']} !important;
        transition: background-color 0.15s ease, box-shadow 0.15s ease !important;
    }}
    .stButton > button:hover {{
        background-color: {t['hover']} !important;
        box-shadow: 0 1px 4px rgba(0,0,0,0.15) !important;
    }}
    .stButton > button[kind="primary"],
    .stButton > button[kind="primary"]:hover {{
        background-color: {t['primary']} !important;
        color: #ffffff !important;
        border-color: {t['primary']} !important;
    }}
    /* The label lives in a nested <p>, which `.stApp *` would paint dark. */
    .stButton > button[kind="primary"] *,
    .stButton > button[kind="primary"]:hover * {{
        color: #ffffff !important;
    }}
    .stDownloadButton > button {{
        background-color: {t['widget_bg']} !important;
        color: {t['text']} !important;
        border: 1px solid {t['border']} !important;
        border-radius: 6px !important;
    }}

    /* File uploader (dropzone uses config secondaryBackgroundColor — force theme) */
    [data-testid="stFileUploaderDropzone"],
    [data-testid="stFileUploader"] section {{
        background-color: {t['widget_bg']} !important;
        border: 1px solid {t['border']} !important;
    }}
    [data-testid="stFileUploaderDropzoneInstructions"],
    [data-testid="stFileUploaderDropzoneInstructions"] * {{
        color: {t['text_muted']} !important;
    }}
    [data-testid="stFileUploader"] button {{
        background-color: {t['bg']} !important;
        color: {t['text']} !important;
        border: 1px solid {t['border']} !important;
    }}

    /* Sidebar exit button: boxed, centered (not the transparent nav style) */
    [data-testid="stSidebar"] .st-key-exit_btn button {{
        background-color: {t['widget_bg']} !important;
        border: 1px solid {t['border']} !important;
        text-align: center !important;
        padding: 0.35rem 0.75rem !important;
        border-radius: 6px !important;
    }}
    [data-testid="stSidebar"] .st-key-exit_btn button:hover {{
        background-color: {t['hover']} !important;
        border-color: {t['primary']} !important;
    }}

    [data-testid="stAlert"], [data-testid="stAlert"] * {{ color: {t['text']} !important; }}

    hr {{ border: none; border-top: 1px solid {t['border']}; margin: 1.25rem 0; }}

    [data-testid="stVerticalBlockBorderWrapper"] > div {{
        border-color: {t['border']} !important;
        background-color: {t['widget_bg']} !important;
    }}

    .stSpinner > div {{ border-top-color: {t['primary']} !important; }}
    [data-testid="stProgressBarTrack"] {{ background-color: {t['border']} !important; }}
    [data-testid="stProgressBarTrack"] > div {{
        background-color: {t['primary']} !important;
    }}

    .block-container {{ padding-top: 1.5rem; padding-bottom: 2rem; }}
    </style>
    """
