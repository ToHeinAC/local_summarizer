# Testing

Run: `uv run pytest`. Tests are fully offline — the summarizer LLM, the
conversion/OCR calls, and the model-availability query are monkeypatched, so no
Ollama server is required. 98 tests total (well under the 200 cap).

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
| `test_agent.py` | chunk split, single-pass vs map-reduce, progress monotonicity, Markdown-first ingest, language resolution, empty input |
| `test_export.py` | md/docx/pdf output validity, unicode, exporters registry |
| `test_auth.py` | env-seeded store, hashed (never plaintext) storage, wrong password, unknown user, missing seed, corrupt/missing store |
| `test_app.py` | UI helpers, accepted formats, config wiring, theme availability, and the two-tab workflow driven through `AppTest` |

## UI tests
`test_app.py` runs the real Streamlit script via `streamlit.testing.v1.AppTest`.
The `anon` fixture stubs `models.annotate_availability` and points
`auth.DATA_ROOT` at `tmp_path`; `at` builds on it by presetting
`session_state["user"]`, i.e. signed in. Signed out, the app must render only the
login form (no tabs); valid credentials sign in, invalid ones error, and Logout
clears the session. It also asserts the tab labels, that the sidebar exposes only the model selector, that language and
template live in tab 2, the radio's default source, button disabled-states, and
that clicking **Summarize** calls `agent.run(text=...)` with no file arguments —
i.e. step 2 never re-runs conversion.

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
