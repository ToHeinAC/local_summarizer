# Architecture

Layered design with a strict boundary: **LangChain/LangGraph only in the agent
layer** (`src/agent.py`, `src/tools.py`). Every other module is plain Python —
no LangChain, no vector DB, no embeddings, no cloud LLM APIs.

Note: `src/ollama_client.py` talks to Ollama directly with the `ollama` package.
That is *not* LangChain, so it stays on the plain-Python side of the boundary —
the same way `models.py` already queries `GET /api/tags` over `urllib`.

## Layers
1. **UI (`app.py`, `theme.py`, `auth.py`, `i18n.py`)** — Streamlit, German by
   default with an English toggle (see [ui.md](ui.md)), gated by a sign-in form
   (`auth.verify`, bcrypt hashes in `data/users.json`); nothing renders until a
   user is in `st.session_state["user"]`. Then a single window: the main panel
   collects the model, the precision (LLM-Markdown) selectbox, the uploaded document,
   the summary language and the template, and one **Zusammenfassen** button calls
   `agent.run(filename=..., data=..., fast=...)` — conversion runs *inside* that
   call, so the UI never touches `extract` directly. The sidebar holds only an
   Advanced-options expander and the language/exit/logout button row. `theme.py` holds the Forest palette and
   the injectable CSS. Calls `agent.run()` and `export.*`; never imports
   LangChain. See [ui.md](ui.md).
2. **Agent (`agent.py`, `tools.py`)** — the LangGraph state machine and the
   LangChain Ollama chat client. See [agent.md](agent.md).
3. **Ingestion (`extract.py`, `md_convert.py`, `ollama_client.py`)** — file
   bytes → Markdown, including vision OCR for scanned PDF pages.
   See [ingestion.md](ingestion.md).
4. **Services (plain Python)** — `i18n.py`, `language.py`, `templates.py`,
   `models.py`, `export.py`, `config.py`, `prompts.py`.

## Data flow
```
uploaded file (pdf/docx/txt/md) + language/template/model
        │
        ▼
agent.run(filename, data, fast=True, template_id, model_id,
          target_language, host, ocr_model, rewrite_model, pdf_dpi, on_progress)
        │  ingest ─ extract.to_markdown(..., fast=True)
        │             └─ md_convert: per PDF page → verbatim text | OCR
        │  → chunk → map → reduce → finalize
        ▼
Markdown summary ──► export.to_{markdown,pdf,docx} ──► download buttons
```
The UI passes the raw file to `agent.run()`; the ingest node converts it (with
`fast=True`, so digital pages are used verbatim). The `text=` path — a
pre-converted string with no file conversion — remains supported for direct API
use and is covered by tests.

## Progress reporting
One callback for the whole run. `agent.run()` receives
`on_progress(fraction, label)`; the graph forwards it via the run config
(`configurable.on_progress`) and each node calls it. In the ingest node,
`_ingest` maps the converter's `(done, total)` into its own `0.0 … INGEST_SHARE`
band. This keeps Streamlit objects out of both the agent and ingestion layers.

## Configuration
`config.py` loads `.env` via `python-dotenv`: `OLLAMA_HOST`, `APP_PORT`, the
default model/template/language ids, and the conversion knobs `OCR_MODEL`,
`REWRITE_MODEL`, `PDF_DPI`. `auth.py` loads `.env` itself for the `SEED_PW_*`
seed passwords, which stay out of `Config` (and out of the repo).

## Theme
Colors live in two places that must agree: `.streamlit/config.toml` (what
Streamlit paints before the app runs) and `theme.FOREST` (what the injected CSS
re-asserts afterwards). See [ui.md](ui.md).
