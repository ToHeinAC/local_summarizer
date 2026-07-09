# Architecture

Layered design with a strict boundary: **LangChain/LangGraph only in the agent
layer** (`src/agent.py`, `src/tools.py`). Every other module is plain Python —
no LangChain, no vector DB, no embeddings, no cloud LLM APIs.

Note: `src/ollama_client.py` talks to Ollama directly with the `ollama` package.
That is *not* LangChain, so it stays on the plain-Python side of the boundary —
the same way `models.py` already queries `GET /api/tags` over `urllib`.

## Layers
1. **UI (`app.py`, `theme.py`)** — Streamlit, two tabs. Tab 1 uploads a document
   and calls `extract.to_markdown()` to convert it, offering the `.md` as a
   download. Tab 2 takes that Markdown (or an uploaded `.md`), collects language
   and template, and calls `agent.run(text=...)`. The sidebar holds only the
   model selector and the safe exit button. `theme.py` holds the Forest palette
   and the injectable CSS. Calls `extract`, `agent.run()` and `export.*`; never
   imports LangChain. See [ui.md](ui.md).
2. **Agent (`agent.py`, `tools.py`)** — the LangGraph state machine and the
   LangChain Ollama chat client. See [agent.md](agent.md).
3. **Ingestion (`extract.py`, `md_convert.py`, `ollama_client.py`)** — file
   bytes → Markdown, including vision OCR for scanned PDF pages.
   See [ingestion.md](ingestion.md).
4. **Services (plain Python)** — `language.py`, `templates.py`, `models.py`,
   `export.py`, `config.py`, `prompts.py`.

## Data flow
```
TAB 1  uploaded file (pdf/docx/txt/md)
        │
        ▼
extract.to_markdown(filename, data, ocr_model, rewrite_model, dpi, host,
                    on_progress)
        │  └─ md_convert: per PDF page → rewrite | OCR
        ▼
Markdown ──► download .md  +  session_state["markdown"]

TAB 2  session Markdown (default) or uploaded .md, + language/template/model
        │
        ▼
agent.run(text, template_id, model_id, target_language, host, on_progress)
        │  ingest → chunk → map → reduce → finalize
        ▼
Markdown summary ──► export.to_{markdown,pdf,docx} ──► download buttons
```
Because the UI converts up front, `agent.run()` is called with `text=` and its
ingest node does no file conversion. The file-based path (`filename`/`data`)
remains supported for direct API use and is covered by tests.

## Progress reporting
Two callbacks, one per step. Conversion reports
`on_progress(done, total, label)` straight to tab 1's progress bar.
Summarization reports `on_progress(fraction, label)` into `agent.run()`; the
graph forwards it via the run config (`configurable.on_progress`) and each node
calls it. When `agent.run()` *is* given a file, `_ingest` maps the converter's
`(done, total)` into its own `0.0 … INGEST_SHARE` band. This keeps Streamlit
objects out of both the agent and ingestion layers.

## Configuration
`config.py` loads `.env` via `python-dotenv`: `OLLAMA_HOST`, `APP_PORT`, the
default model/template/language ids, and the conversion knobs `OCR_MODEL`,
`REWRITE_MODEL`, `PDF_DPI`.

## Theme
Colors live in two places that must agree: `.streamlit/config.toml` (what
Streamlit paints before the app runs) and `theme.FOREST` (what the injected CSS
re-asserts afterwards). See [ui.md](ui.md).
