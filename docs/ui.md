# UI & theme

Visual style ported from
[ToHeinAC/KB_BS_local-wiki-he](https://github.com/ToHeinAC/KB_BS_local-wiki-he)
(Apache-2.0) so both apps look like one family. Only that repo's default
**Forest** theme is ported; its second theme and in-app switcher are not.

## Palette (`src/theme.py`)
| Key | Value | Use |
|---|---|---|
| `bg` | `#f6f7f2` | page background |
| `sidebar_bg` | `#eaf0ec` | sidebar |
| `widget_bg` | `#ffffff` | inputs, buttons, cards |
| `text` | `#1a1f1c` | all text |
| `text_muted` | `#5a6b5e` | captions, placeholders |
| `primary` | `#234637` | primary button, spinner, progress |
| `border` | `#d4dbd6` | borders, dividers |
| `hover` | `rgba(35,70,55,0.10)` | hover fill |

`build_css(t=FOREST) -> str` returns the `<style>` block; `app.py` injects it
with `st.markdown(..., unsafe_allow_html=True)`.

**These values are duplicated in `.streamlit/config.toml`** — Streamlit paints
the shell from the TOML before Python runs, so both must be kept in sync.

## Fonts
- Body/UI: **Inter** (400/500/600), 15px base.
- Headings `h1..h3`: **Libre Baskerville**, serif, weight 700.
- Both are pulled from Google Fonts by a single `@import` in the CSS, so first
  paint needs network access. Everything else runs offline; without it the
  fallbacks (`system-ui`, `Georgia`) apply.

## Gotcha: progress bar track vs. fill
Streamlit renders `div[role="progressbar"] > div[data-testid="stProgressBarTrack"]
> div`, where the inner div is the **fill** — it is `width: 100%` and reveals
progress via `transform: translateX(value - 100%)`. Colouring the *track*
(`div[role="progressbar"] > div`) with `primary` therefore paints the whole bar
green and it looks 100% full at every value. Style
`[data-testid="stProgressBarTrack"] > div` for the fill and the track itself for
the groove.

## Gotcha: Material icon ligatures
The CSS sets `color` on `.stApp *` but deliberately **does not** set
`font-family` there. A global `font-family` overrides Streamlit's Material icon
font, and the icons then render as literal text ("keyboard_arrow_down") instead
of glyphs. The icon font is re-asserted explicitly for
`[data-testid="stIconMaterial"]` and friends.

## Gotcha: primary button labels
`.stApp *` sets `color` on every element, and a button's label is a nested `<p>`,
not the `<button>` itself. Setting `color: #fff` on
`.stButton > button[kind="primary"]` alone leaves the label dark — the `<p>` is
matched directly by `.stApp *`, which beats inheriting from its parent. The
white must be re-asserted on the descendants
(`... button[kind="primary"] *`).

## GUI language
**German by default, English on request.** Every user-facing string comes from
`src/i18n.py`: `t(key, lang, **fmt)` for UI copy, `pick(field, lang)` for the
per-language `label`/`note`/`description` dicts that `models.py` and
`templates.py` carry next to the data they describe.

The current language lives in `st.session_state["ui_lang"]` (default `"de"`,
read by `app._ui_lang()`). `app._language_toggle(container)` renders one button
(`key="lang_btn"`) into the container it's given, labelled with the *other*
language — `🌐 English` while in German — which flips the state and reruns. When
signed in it sits at the bottom of the sidebar, directly below **Abmelden**; the
same button is also drawn under the login form, so an anonymous visitor can switch
before signing in. **Logout preserves `ui_lang`** while `st.session_state.clear()`
drops everything else, so the chosen language survives a logout while nothing else
does.

Progress-bar labels are built in `agent.py` and `md_convert.py`, which are below
the UI layer, so the language is passed down explicitly: `agent.run(ui_lang=...)`
→ `SummaryState["ui_lang"]`, and `extract.to_markdown(lang=...)` →
`md_convert.pdf_to_markdown(..., lang)`. Both default to German.

Strings the **LLM** reads stay English regardless of the GUI language:
everything in `prompts.py` (including `LANGUAGE_LABELS`) and each template's
`structure`. The summary-language selectbox therefore renders
`i18n.LANGUAGE_NAMES`, which maps each ISO code to its name in *both* GUI
languages — a missing entry would be a `KeyError` in `format_func`, which
`test_app.py` and `test_i18n.py` guard.

`auth.ensure_seeded()` raises its "no seed passwords" `RuntimeError` in English:
it is an ops/config error, and `main()` catches it and renders the translated
`seed_missing` string instead of the raw message.

## Sign-in gate
`main()` calls `auth.ensure_seeded()` then `_login_gate()` before the sidebar and
main panel. Signed out, the page is a centered `st.columns([1, 1.4, 1])` block holding
the title, the caption *Zum Fortfahren anmelden*, an `st.form("login_form")`
with Benutzername, a `type="password"` field, a primary **Anmelden** button, and
the language toggle; a bad credential pair renders `st.error`. `st.stop()` ends the script run, so nothing
else is ever rendered to an anonymous visitor. Same shape as the reference repo.

On success the username goes into `st.session_state["user"]` and the script
reruns. The sidebar then ends with `Angemeldet als **<user>**`, the language
toggle, and one boxed **Abmelden** button (`key="logout_btn"`). Logout is
optional — Abmelden simply calls `st.session_state.clear()` (dropping the summary)
and reruns; it kills no process, so the app (and any Cloudflare tunnel in front of
it) stays alive. There is deliberately **no in-app exit button**: SIGTERMing the
app would trip `tunnel.sh`'s watchdog and tear down the public URL. Stop the app
from the terminal (`./tunnel.sh stop`). Passwords
live as bcrypt hashes in `data/users.json`, seeded once from the `SEED_PW_*`
variables in `.env` (see [../src/auth.py](../src/auth.py)). A missing seed raises,
and `main()` renders that as an `st.error` instead of a traceback.

## Single-window workflow
The main area is one panel — no tabs. Top to bottom:

1. an intro caption, then a `---` divider;
2. **quality parameters** in a 2-column row — the **Modell** selector (with its
   speed/quality stars and note, rendered by `_model_selector`) and, beside it
   under a **PRÄZISION PDF** caption, a `st.selectbox` choosing **Schnellmodus
   (wörtlich)** (default) or **Genaues Markdown (LLM)**, with a `help` tooltip
   explaining the cost. Below it, speed/quality stars flip with the choice —
   fast = Speed ★★★ / Quality ★☆☆, precise = Speed ★☆☆ / Quality ★★★;
3. the summary **Sprache** (with an **Auswahl** caption below it) and **Vorlage**
   selectboxes in a 2-column row, then a `---` divider;
4. a file uploader accepting **PDF/DOCX/TXT/MD**;
5. one primary **Zusammenfassen** button (disabled until a file is uploaded and
   the chosen model is installed).

The model selector lives in the main panel (not the sidebar), next to the
precision selectbox it pairs with.

Clicking it runs `app._run()`, which calls
`agent.run(filename=..., data=..., fast=not llm_format, return_markdown=llm_format, ...)`
— a single pass that converts the upload *and* summarizes it. With the fast option
(`fast=True`) conversion is **plain text** (digital PDF pages verbatim, scanned
pages OCR'd; no per-page LLM rewrite); with the precise option (`fast=False`) each
text page is LLM-formatted first (one call per page, wording preserved). See
[ingestion.md](ingestion.md). On success the summary is stored in
`st.session_state["summary"]` (with the filename `["stem"]`), rendered in a
bordered container, and offered as `.md` / `.docx` / `.pdf` downloads. In the
precise mode `agent.run(return_markdown=True)` also returns the generated document
Markdown; it is stored in `st.session_state["converted_md"]` and offered as a
separate **Erzeugtes Markdown herunterladen (.md)** download above the summary (in
fast mode that key is `None` and no such button shows). `summary` / `converted_md`
/ `stem` are the session keys the flow writes.

## Layout conventions
- `layout="wide"`, sidebar `expanded`.
- Sidebar title `## 📝 KI-Zusammenfassung`, then `---` dividers. The sidebar holds
  only the **Advanced options** expander and, at the bottom, the signed-in caption
  above two stacked full-width buttons: **Abmelden**, then the GUI-language toggle.
  Everything else — the model selector, the *summary* language and the template —
  lives in the main panel, next to the work it affects.
- **Advanced options** (`st.expander`, collapsed) holds a *Clear CUDA memory*
  button (`ollama_client.unload_all`).
- Section labels are ALL-CAPS `st.caption()` (MODELL / PRÄZISION PDF / SPRACHE /
  VORLAGE) above `label_visibility="collapsed"` widgets.
- **Zusammenfassen** is `type="primary"` (filled green). Summary downloads are
  `use_container_width=True` in a 3-column row.
- The summary renders inside `st.container(border=True)`.
- The language and logout buttons use `key="lang_btn"` / `key="logout_btn"`, which
  the CSS targets via `.st-key-*` to give them a boxed style instead of the
  transparent sidebar-nav look (the CSS also forces them `width: 100%`). Both are
  full-width buttons stacked on their own lines: **Abmelden**, then language toggle.
  There is no exit button — see the sign-in gate note on why (tunnel preservation).
