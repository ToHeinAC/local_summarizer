# Architecture

Layered design with a strict boundary: **LangChain/LangGraph only in the agent
layer** (`src/agent.py`, `src/tools.py`). Every other module is plain Python —
no LangChain, no vector DB, no embeddings, no cloud LLM APIs.

Note: `src/ollama_client.py` talks to Ollama directly with the `ollama` package.
That is *not* LangChain, so it stays on the plain-Python side of the boundary —
the same way `models.py` already queries `GET /api/tags` over `urllib`.

## Layers
1. **UI (`app.py`, `theme.py`)** — Streamlit. Renders the sidebar (language,
   template, model), the file uploader, the progress bar, the rendered summary,
   and the three download buttons. Owns the safe exit button. `theme.py` holds
   the Forest palette and the injectable CSS. Calls `agent.run()` and
   `export.*`; never imports LangChain. See [ui.md](ui.md).
2. **Agent (`agent.py`, `tools.py`)** — the LangGraph state machine and the
   LangChain Ollama chat client. See [agent.md](agent.md).
3. **Ingestion (`extract.py`, `md_convert.py`, `ollama_client.py`)** — file
   bytes → Markdown, including vision OCR for scanned PDF pages.
   See [ingestion.md](ingestion.md).
4. **Services (plain Python)** — `language.py`, `templates.py`, `models.py`,
   `export.py`, `config.py`, `prompts.py`.

## Data flow
```
uploaded file + sidebar options
        │
        ▼
agent.run(filename, data, template_id, model_id, target_language,
          host, ocr_model, rewrite_model, pdf_dpi, on_progress)
        │  ingest → chunk → map → reduce → finalize
        │  └─ ingest: extract.to_markdown → md_convert (rewrite | OCR)
        ▼
Markdown summary ──► export.to_{markdown,pdf,docx} ──► download buttons
```

## Progress reporting
The UI passes an `on_progress(fraction, label)` callback into `agent.run()`.
The graph forwards it via the run config (`configurable.on_progress`) and each
node calls it. `md_convert` reports with a different signature —
`on_progress(done, total, label)` — which `_ingest` maps into the graph's
`0.0 … INGEST_SHARE` band. This keeps Streamlit objects out of both the agent
and ingestion layers and makes them independently testable.

## Configuration
`config.py` loads `.env` via `python-dotenv`: `OLLAMA_HOST`, `APP_PORT`, the
default model/template/language ids, and the conversion knobs `OCR_MODEL`,
`REWRITE_MODEL`, `PDF_DPI`.

## Theme
Colors live in two places that must agree: `.streamlit/config.toml` (what
Streamlit paints before the app runs) and `theme.FOREST` (what the injected CSS
re-asserts afterwards). See [ui.md](ui.md).
