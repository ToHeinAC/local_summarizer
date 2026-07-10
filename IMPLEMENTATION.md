# IMPLEMENTATION

Current implementation state of Local Summarizer. Compact by design; deep
detail lives in [docs/](docs/). See [PRD.md](PRD.md) for goals and
[AGENTS.md](AGENTS.md) for collaboration rules.

## Status
All planned features implemented and tested (83 tests passing). End-to-end
verified against a live Ollama server, including OCR of a scanned PDF.

## Architecture (one screen)
Layered. LangChain/LangGraph are confined to the **agent layer**
(`src/agent.py`, `src/tools.py`); everything else is plain Python.
`ollama_client.py` uses the plain `ollama` package, not LangChain.

```
app.py ─ Streamlit UI: 2 tabs, progress, downloads, exit  (no LangChain)
  ├─ theme.py       Forest palette + injected CSS
  ├─ TAB 1 ─ extract.py       file bytes → Markdown  (→ download .md)
  │            └─ md_convert.py  PDF per-page rewrite/OCR, DOCX→MD
  │                 └─ ollama_client.py  vision OCR + text rewrite
  └─ TAB 2 ─ agent.run() ─ LangGraph: ingest→chunk→map→reduce→finalize
       ├─ tools.py         ChatOllama wrapper        (LangChain OK)
       ├─ language.py      detect source language
       ├─ templates.py     template registry
       ├─ models.py        model registry + availability
       ├─ export.py        summary → md/pdf/docx
       ├─ prompts.py       all prompt constants
       └─ config.py        dotenv config
```

Data flow, two explicit steps:

1. **Convert (tab 1)** — the uploaded file goes to `extract.to_markdown()`
   (per-page: digital PDF text is LLM-rewritten, scanned pages are OCR'd by a
   vision model). The Markdown is shown, downloadable as `.md`, and kept in
   `st.session_state["markdown"]`.
2. **Summarize (tab 2)** — that Markdown (default) or a user-uploaded `.md`,
   plus the language and template chosen there, goes to `agent.run(text=...)`,
   which detects language, chunks, map-reduces via the selected Ollama model,
   and finalizes → `export.py` produces download bytes.

Each step has its own progress callback, so Streamlit stays out of the agent and
ingestion layers. Details: [docs/architecture.md](docs/architecture.md),
[docs/agent.md](docs/agent.md), [docs/ingestion.md](docs/ingestion.md),
[docs/ui.md](docs/ui.md).

## Module map
| Module | Role | Docs |
|---|---|---|
| `src/app.py` | Streamlit UI: convert tab, summarize tab, sidebar, exit | [ui](docs/ui.md) |
| `src/theme.py` | Forest palette + injectable CSS | [ui](docs/ui.md) |
| `src/agent.py` | LangGraph map-reduce summarizer + `run()` entry point | [agent](docs/agent.md) |
| `src/tools.py` | `ChatOllama` factory + prompt runner | [agent](docs/agent.md) |
| `src/extract.py` | PDF/DOCX/TXT/MD → Markdown (dispatch) | [ingestion](docs/ingestion.md) |
| `src/md_convert.py` | PDF per-page rewrite/OCR routing, DOCX → Markdown | [ingestion](docs/ingestion.md) |
| `src/ollama_client.py` | Plain-Python Ollama: `ocr`, `rewrite`, `unload` | [ingestion](docs/ingestion.md) |
| `src/language.py` | `langdetect` source-language detection | [ingestion](docs/ingestion.md) |
| `src/templates.py` | Summary template registry | [templates](docs/templates.md) |
| `src/models.py` | Model registry + Ollama availability check | [models](docs/models.md) |
| `src/export.py` | Markdown → md/pdf/docx bytes | [export](docs/export.md) |
| `src/prompts.py` | Named prompt constants | [agent](docs/agent.md) |
| `src/config.py` | dotenv-backed config | — |

## Key decisions
- **Two-step UI**: conversion and summarization are separate tabs. The user can
  inspect and download the intermediate Markdown, fix it, and feed a corrected
  `.md` back into step 2 — conversion is the expensive, error-prone half, so it
  is worth making it a visible artifact rather than a hidden stage.
- **Markdown-first ingestion**: every upload becomes Markdown before
  summarization. PDF pages are routed per page — a text layer ≥ 40 chars is
  LLM-rewritten (wording preserved); anything less is rasterized and OCR'd by a
  vision model. Ported from
  [KB_BS_local-wiki-he](https://github.com/ToHeinAC/KB_BS_local-wiki-he)
  (Apache-2.0). See [docs/ingestion.md](docs/ingestion.md).
- **OCR is an Ollama vision model** (`deepseek-ocr:3b`), not tesseract — keeps
  the app offline with no system binaries.
- **Cost**: the per-page rewrite means a digital PDF costs one LLM call per page
  before summarizing. Deliberate, matching the reference repo; set
  `REWRITE_MODEL` to a fast model for large documents.
- **Theme**: Forest palette (green/cream), Inter + Libre Baskerville, ported
  from the same repo. Colors are duplicated in `.streamlit/config.toml` and
  `theme.FOREST` and must stay in sync. See [docs/ui.md](docs/ui.md).
- **Models**: `gemma4:e2b` (fast), `gemma4:e4b` (standard, default),
  `qwen3:14b` (smarter), `gpt-oss:20b` (accurate). Tags match `ollama list`.
  Uninstalled models are flagged in the UI. See [docs/models.md](docs/models.md).
- **PDF export**: `fpdf2` (pure Python). Uses a system DejaVu Unicode font when
  present, else Helvetica with latin-1 fallback. See [docs/export.md](docs/export.md).
- **Formats in**: PDF, DOCX, TXT, MD (step 1); MD only (step 2's own upload).
  **Formats out**: MD (step 1), MD/PDF/DOCX (step 2).
- **Chunking**: character-bounded (6000/200 overlap); single-chunk documents
  skip the map/reduce passes. See [docs/agent.md](docs/agent.md).

## Run & test
```bash
uv run streamlit run src/app.py --server.port 8530
uv run pytest
./tunnel.sh                     # optional: public URL via Cloudflare quick tunnel
./tunnel.sh stop                # shut the app + tunnel down again
```
Test map: [docs/testing.md](docs/testing.md).

`tunnel.sh` starts the app if needed, then exposes port 8530 as a temporary
`*.trycloudflare.com` URL (no Cloudflare account; needs `cloudflared`). It moves
any named-tunnel config aside to force quick-tunnel mode and restores it once the
tunnel has registered. Ported from
[KB_BS_local-wiki-he](https://github.com/ToHeinAC/KB_BS_local-wiki-he).

**Persistence.** The app and the tunnel are started with `setsid nohup`, so they
get their own session *and* ignore `SIGHUP`; closing the terminal leaves both
running. The script itself returns as soon as the URL is printed. A detached
watchdog stops the tunnel once port 8530 stops listening, so the in-app exit
button still tears the whole thing down. `./tunnel.sh stop` kills both.

`setsid` alone is not enough: it removes the controlling terminal but leaves
`SIGHUP` at its default action, so anything that signals the process group still
kills the app. `nohup` supplies the ignore. The watchdog is passed the tunnel's
PID as an argument rather than a `pkill -f` pattern — a pattern would appear in
the watchdog's own command line and it would kill itself.

## Known constraints
- Requires a reachable Ollama server (`OLLAMA_HOST`, default
  `http://localhost:11434`). Summarizing a PDF also needs `OCR_MODEL` pulled.
- Port 8530 is mandated by the PRD; free it if another app holds it.
- The theme's webfonts load from Google Fonts on first paint; without network
  access the app still runs and falls back to `system-ui` / `Georgia`.
