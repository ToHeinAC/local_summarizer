# Architecture

Layered design with a strict boundary: **LangChain/LangGraph only in the agent
layer** (`src/agent.py`, `src/tools.py`). Every other module is plain Python —
no LangChain, no vector DB, no embeddings, no cloud LLM APIs.

## Layers
1. **UI (`app.py`)** — Streamlit. Renders the sidebar (language, template,
   model), the file uploader, the progress bar, the rendered summary, and the
   three download buttons. Owns the safe exit button. Calls `agent.run()` and
   `export.*`; never imports LangChain.
2. **Agent (`agent.py`, `tools.py`)** — the LangGraph state machine and the
   Ollama client. See [agent.md](agent.md).
3. **Services (plain Python)** — `extract.py`, `language.py`, `templates.py`,
   `models.py`, `export.py`, `config.py`, `prompts.py`.

## Data flow
```
uploaded file + sidebar options
        │
        ▼
agent.run(filename, data, template_id, model_id, target_language, host, on_progress)
        │  ingest → chunk → map → reduce → finalize
        ▼
Markdown summary ──► export.to_{markdown,pdf,docx} ──► download buttons
```

## Progress reporting
The UI passes an `on_progress(fraction, label)` callback into `agent.run()`.
The graph forwards it via the run config (`configurable.on_progress`) and each
node calls it. This keeps Streamlit objects out of the agent layer and makes
the agent independently testable.

## Configuration
`config.py` loads `.env` via `python-dotenv`: `OLLAMA_HOST`, `APP_PORT`, and the
default model/template/language ids.
