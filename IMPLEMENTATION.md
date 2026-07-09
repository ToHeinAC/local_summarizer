# IMPLEMENTATION

Current implementation state of Local Summarizer. Compact by design; deep
detail lives in [docs/](docs/). See [PRD.md](PRD.md) for goals and
[AGENTS.md](AGENTS.md) for collaboration rules.

## Status
All planned features implemented and tested (46 tests passing). End-to-end
verified against a live Ollama server.

## Architecture (one screen)
Layered. LangChain/LangGraph are confined to the **agent layer**
(`src/agent.py`, `src/tools.py`); everything else is plain Python.

```
app.py ─ Streamlit UI, progress, downloads, exit   (no LangChain)
  └─ agent.run() ─ LangGraph: ingest→chunk→map→reduce→finalize
       ├─ tools.py     ChatOllama wrapper           (LangChain OK)
       ├─ extract.py   file bytes → text
       ├─ language.py  detect source language
       ├─ templates.py template registry
       ├─ models.py    model registry + availability
       ├─ export.py    summary → md/pdf/docx
       ├─ prompts.py   all prompt constants
       └─ config.py    dotenv config
```

Data flow: `app.py` collects sidebar options + uploaded file → `agent.run()`
extracts text, detects language, chunks, map-reduces via the selected Ollama
model, and finalizes with the chosen template/language → `export.py` produces
download bytes. Progress is pushed through an `on_progress(fraction, label)`
callback so Streamlit stays out of the agent layer.
Details: [docs/architecture.md](docs/architecture.md),
[docs/agent.md](docs/agent.md).

## Module map
| Module | Role | Docs |
|---|---|---|
| `src/app.py` | Streamlit UI: sidebar, upload, progress, downloads, exit | [architecture](docs/architecture.md) |
| `src/agent.py` | LangGraph map-reduce summarizer + `run()` entry point | [agent](docs/agent.md) |
| `src/tools.py` | `ChatOllama` factory + prompt runner | [agent](docs/agent.md) |
| `src/extract.py` | PDF/DOCX/TXT/MD → text | [ingestion](docs/ingestion.md) |
| `src/language.py` | `langdetect` source-language detection | [ingestion](docs/ingestion.md) |
| `src/templates.py` | Summary template registry | [templates](docs/templates.md) |
| `src/models.py` | Model registry + Ollama availability check | [models](docs/models.md) |
| `src/export.py` | Markdown → md/pdf/docx bytes | [export](docs/export.md) |
| `src/prompts.py` | Named prompt constants | [agent](docs/agent.md) |
| `src/config.py` | dotenv-backed config | — |

## Key decisions
- **Models**: `gemma4:e2b` (fast), `gemma4:e4b` (standard, default),
  `qwen3:14b` (smarter), `gpt-oss:20b` (accurate). Tags match `ollama list`.
  Uninstalled models are flagged in the UI. See [docs/models.md](docs/models.md).
- **PDF**: `fpdf2` (pure Python). Uses a system DejaVu Unicode font when
  present, else Helvetica with latin-1 fallback. See [docs/export.md](docs/export.md).
- **Formats in**: PDF, DOCX, TXT, MD. **Formats out**: MD, PDF, DOCX.
- **Chunking**: character-bounded (6000/200 overlap); single-chunk documents
  skip the map/reduce passes. See [docs/agent.md](docs/agent.md).

## Run & test
```bash
uv run streamlit run src/app.py --server.port 8506
uv run pytest
```
Test map: [docs/testing.md](docs/testing.md).

## Known constraints
- Requires a reachable Ollama server (`OLLAMA_HOST`, default
  `http://localhost:11434`).
- Port 8506 is mandated by the PRD; free it if another app holds it.
