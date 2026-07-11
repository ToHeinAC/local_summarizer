# Testing

Run: `uv run pytest`. Tests are fully offline — the summarizer LLM, the
conversion/OCR calls, and the model-availability query are monkeypatched, so no
Ollama server is required. 110 tests total (well under the 200 cap).

| File | Covers |
|---|---|
| `test_config.py` | defaults + env overrides, incl. `OCR_MODEL`/`REWRITE_MODEL`/`PDF_DPI` |
| `test_prompts.py` | prompt constants and their `{}` slots, OCR/rewrite prompt invariants |
| `test_extract.py` | pdf/docx/txt/md → Markdown, rewrite vs OCR routing, unsupported/no extension, stripping |
| `test_md_convert.py` | text-layer detection, OCR prompt selection, DOCX headings/lists/tables/order, VRAM unload, page progress |
| `test_theme.py` | palette keys, CSS `<style>` block, font imports, icon-font guard |
| `test_language.py` | English/German detection, fallbacks |
| `test_models.py` | registry shape, default, availability annotation, unreachable server |
| `test_templates.py` | registry shape, default, unknown id |
| `test_agent.py` | chunk split, single-pass vs map-reduce, progress monotonicity, Markdown-first ingest, `fast=True` skips the per-page rewrite, language resolution, empty input |
| `test_export.py` | md/docx/pdf output validity, unicode, exporters registry |
| `test_auth.py` | env-seeded store, hashed (never plaintext) storage, wrong password, unknown user, missing seed, corrupt/missing store |
| `test_app.py` | UI helpers, accepted formats, config wiring, theme availability, the GUI-language toggle, and the single-window upload→summary flow driven through `AppTest` |
| `test_i18n.py` | catalogue key/placeholder parity across languages, `t` formatting + fallback, `pick` |

## UI tests
`test_app.py` runs the real Streamlit script via `streamlit.testing.v1.AppTest`.
The `anon` fixture stubs `models.annotate_availability` and points
`auth.DATA_ROOT` at `tmp_path`; `at` builds on it by presetting
`session_state["user"]`, i.e. signed in. Signed out, the app must render only the
login form (no tabs); valid credentials sign in, invalid ones error, and
**Abmelden** clears the session. Widget labels are asserted in German (the
default). Clicking `lang_btn` must flip `session_state["ui_lang"]`, relabel every
surface in English, survive Logout, and reach `agent.run(ui_lang=...)`.
`i18n.LANGUAGE_NAMES` is checked to cover every `LANGUAGE_LABELS` code. It also
asserts that there are no tabs, that the sidebar exposes only the model selector,
that language and template live in the main panel, the **Zusammenfassen**
disabled-state (until a file is uploaded via `file_uploader.set_value`), and that
clicking it calls `agent.run(filename=..., data=..., fast=True)` with no `text=`
argument — i.e. the single click converts and summarizes in one pass.

## Fixtures (`conftest.py`)
In-memory sample documents (`txt_bytes`, `md_bytes`, `docx_bytes`, `pdf_bytes`,
`scanned_pdf_bytes`), a `FakeLLM`, and `stub_ollama` (a `StubOllama` patching
`ollama_client.ocr/rewrite/unload` and recording calls).

`scanned_pdf_bytes` is a PDF page with **no text layer**, so it exercises the
OCR branch of the per-page router; `pdf_bytes` has one and exercises the rewrite
branch.

Edge cases covered: empty document, unsupported/no extension, multi-chunk
map-reduce, undetectable language, unreachable Ollama, unicode PDF, a page whose
text layer is below `TEXT_THRESHOLD` (page numbers only), progress running
backwards, and OCR-model eviction only when OCR actually ran.

## What the tests do not cover
The stubs assert *which* model each page is routed to, not OCR quality. Both
paths were verified manually against a live Ollama (`deepseek-ocr:3b` on a
rasterized scan, `gemma4:e2b` on a digital page).
