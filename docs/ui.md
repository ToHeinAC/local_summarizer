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

## Two-tab workflow
The main area is `st.tabs(["1 · Convert", "2 · Summarize"])`:

1. **Convert** — upload a PDF/DOCX/TXT/MD, press **Convert to Markdown**. The UI
   calls `extract.to_markdown()` directly (plain Python, no agent) and stores the
   result in `st.session_state["markdown"]` plus the filename `["stem"]`. The
   Markdown is previewed in a scrolling bordered container and downloadable as
   `.md`. A fresh conversion clears any stale `["summary"]`.
2. **Summarize** — a radio picks the source: `SOURCE_STEP1` (step 1's Markdown,
   the default once it exists) or `SOURCE_UPLOAD` (a `.md` upload — **only** `.md`
   is accepted here). Language and template are chosen in a 2-column row, then
   **Summarize** calls `agent.run(text=...)`. No re-conversion happens, so no
   OCR/rewrite arguments are passed.

Session keys `markdown` / `stem` are the only handoff between the tabs.

## Layout conventions
- `layout="wide"`, sidebar `expanded`.
- Sidebar title `## 📝 Summarizer`, then `---` dividers. The sidebar holds
  **only** the model selector and the exit button; language and template live in
  tab 2, next to the work they affect.
- Section labels are ALL-CAPS `st.caption()` (MODEL / LANGUAGE / TEMPLATE) above
  `label_visibility="collapsed"` selectboxes.
- **Convert to Markdown** and **Summarize** are `type="primary"` (filled green).
  Summary downloads are `use_container_width=True` in a 3-column row.
- Markdown and summary render inside `st.container(border=True)`.
- The exit button uses `key="exit_btn"`, which the CSS targets via
  `.st-key-exit_btn` to give it a boxed style instead of the transparent
  sidebar-nav look. It SIGTERMs the app's own PID only.
