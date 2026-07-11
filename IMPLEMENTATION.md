# IMPLEMENTATION

Current implementation state of Local Summarizer. Compact by design; deep
detail lives in [docs/](docs/). See [PRD.md](PRD.md) for goals and
[AGENTS.md](AGENTS.md) for collaboration rules.

## Status
All planned features implemented and tested (110 tests passing). End-to-end
verified against a live Ollama server, including OCR of a scanned PDF.

## Architecture (one screen)
Layered. LangChain/LangGraph are confined to the **agent layer**
(`src/agent.py`, `src/tools.py`); everything else is plain Python.
`ollama_client.py` uses the plain `ollama` package, not LangChain.

```
app.py ─ Streamlit UI: login gate, single window, progress, downloads, exit  (no LangChain)
  ├─ auth.py        bcrypt user store (data/users.json)
  ├─ i18n.py        German (default) / English UI strings
  ├─ theme.py       Forest palette + injected CSS
  └─ agent.run(filename=…, fast=True) ─ LangGraph: ingest→chunk→map→reduce→finalize
       ├─ extract.py       file bytes → plain text   (called inside ingest)
       │    └─ md_convert.py  PDF per-page verbatim/OCR, DOCX→MD
       │         └─ ollama_client.py  vision OCR (rewrite unused in fast mode)
       ├─ tools.py         ChatOllama wrapper        (LangChain OK)
       ├─ language.py      detect source language
       ├─ templates.py     template registry
       ├─ models.py        model registry + availability
       ├─ export.py        summary → md/pdf/docx
       ├─ prompts.py       all prompt constants
       └─ config.py        dotenv config
```

Sign-in gates everything: `app.py` calls `auth.verify()` before the window is
rendered (see [docs/ui.md](docs/ui.md)). One-click flow:

- **Upload & summarize** — in the main panel pick the model and precision
  selectbox (quality parameters), upload a **PDF/DOCX/TXT/MD**, then pick summary
  language and template, press **Zusammenfassen**. That single click calls
  `agent.run(filename=…, data=…, fast=…)`: the ingest node converts the file to
  text (`fast=True` → digital PDF pages verbatim; the precise option flips it to
  `fast=False` → per-page LLM rewrite; scanned pages always OCR'd by a vision
  model), detects language, chunks, map-reduces via the selected Ollama model, and
  finalizes → `export.py` produces the `.md`/`.pdf`/`.docx` download bytes. No
  intermediate Markdown is shown.

The one progress callback threads through the whole run, so Streamlit stays out
of the agent and ingestion layers. Details: [docs/architecture.md](docs/architecture.md),
[docs/agent.md](docs/agent.md), [docs/ingestion.md](docs/ingestion.md),
[docs/ui.md](docs/ui.md).

## Module map
| Module | Role | Docs |
|---|---|---|
| `src/app.py` | Streamlit UI: login gate, single upload→summary window, sidebar, exit | [ui](docs/ui.md) |
| `src/auth.py` | bcrypt user store + `verify()` | [ui](docs/ui.md) |
| `src/i18n.py` | German/English UI strings, `t()` / `pick()` | [ui](docs/ui.md) |
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
- **Authentication**: a bcrypt-hashed user store in `data/users.json` (gitignored),
  seeded on first run from the `SEED_PW_*` variables in `.env` (`auth.SEED_USERS`
  maps each account to its variable), so no password is ever committed. Ported from
  [KB_BS_local-wiki-he](https://github.com/ToHeinAC/KB_BS_local-wiki-he) without
  its per-database access and maintainer layers — this app has no per-user data,
  so a user is either signed in or not. Delete `data/users.json` to re-seed.
- **Bilingual UI, German by default**: every user-facing string lives in
  `src/i18n.py`; a sidebar button toggles German ↔ English and the choice is kept
  in `session_state["ui_lang"]` (it survives Logout). Model and template labels
  are per-language dicts in their own registries. Progress labels are built in
  the agent/ingestion layers, so the language is passed down explicitly
  (`agent.run(ui_lang=...)`, `extract.to_markdown(lang=...)`). Strings the LLM
  reads stay English — `prompts.py` and each template's `structure` — so
  `i18n.LANGUAGE_NAMES` holds the display names for the summary-language codes
  while `prompts.LANGUAGE_LABELS` keeps the English ones the finalize prompt
  needs. See [docs/ui.md](docs/ui.md).
- **Single-window, one-click flow**: settings (model, summary language,
  template) and the file upload live on one screen; pressing **Zusammenfassen**
  converts *and* summarizes in a single `agent.run(filename=…, fast=…)` pass
  (`fast=True` by default, `fast=False` when the precise option is selected).
  No separate convert step and no intermediate Markdown to inspect or download —
  the earlier two-tab, download-the-`.md`-first workflow was dropped as friction.
- **Plain-text conversion (default) + precision selectbox**: the UI converts with
  `fast=True` by default — digital PDF pages use their extracted text layer
  verbatim (zero LLM rewrite calls); scanned pages still OCR. Trade-off: plainer
  text and raw reading order on multi-column layouts, in exchange for a
  near-instant, byte-exact conversion. A main-panel selectbox (*Schnellmodus
  (wörtlich)* by default, or *Genaues Markdown (LLM)*) opts into the per-page
  LLM-rewrite path (`fast=False`), which formats each text page
  (headings/lists/tables) without changing wording at the cost of one LLM call
  per page.
- **Markdown-first ingestion**: every upload becomes text before
  summarization. PDF pages are routed per page — a text layer ≥ 40 chars is used
  verbatim (or, with `fast=False`, LLM-rewritten with wording preserved);
  anything less is rasterized and OCR'd by a vision model. Ported from
  [KB_BS_local-wiki-he](https://github.com/ToHeinAC/KB_BS_local-wiki-he)
  (Apache-2.0). See [docs/ingestion.md](docs/ingestion.md).
- **OCR is an Ollama vision model** (`deepseek-ocr:3b`), not tesseract — keeps
  the app offline with no system binaries.
- **Cost**: because the UI converts with `fast=True`, a digital PDF adds **no**
  LLM calls before summarizing (its text layer is used verbatim); only scanned
  pages cost a vision-model OCR call. The `fast=False` per-page rewrite (one LLM
  call per page) remains available to API callers. See [docs/ingestion.md](docs/ingestion.md).
- **Performance**: two capped-cost decisions keep the local LLM fast. (1) Every
  Ollama call pins `num_ctx` (8192 for text, 16384 for OCR) — Ollama otherwise
  allocates each model's full 128k window, ballooning VRAM and cutting
  throughput ~5× with no benefit for these small prompts. (2) Scanned PDF pages
  are OCR'd concurrently (`md_convert.MAX_CONVERT_WORKERS=4`); this needs
  `OLLAMA_NUM_PARALLEL≥2` on the Ollama server to matter (~1.9× on a 6-page PDF).
  Both cost no precision. See [docs/ingestion.md](docs/ingestion.md),
  [docs/agent.md](docs/agent.md).
- **Theme**: Forest palette (green/cream), Inter + Libre Baskerville, ported
  from the same repo. Colors are duplicated in `.streamlit/config.toml` and
  `theme.FOREST` and must stay in sync. See [docs/ui.md](docs/ui.md).
- **Models**: `LiquidAI/lfm2.5-1.2b-instruct:latest` (fast), `gemma4:e4b` (standard, default),
  `qwen3:14b` (smarter), `gpt-oss:20b` (accurate). Tags match `ollama list`.
  Uninstalled models are flagged in the UI. See [docs/models.md](docs/models.md).
- **PDF export**: `fpdf2` (pure Python). Uses a system DejaVu Unicode font when
  present, else Helvetica with latin-1 fallback. See [docs/export.md](docs/export.md).
- **Formats in**: PDF, DOCX, TXT, MD. **Formats out**: MD/PDF/DOCX (the summary).
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
- Sign-in protects the UI, not the data: `data/users.json` holds only password
  hashes, but the app itself serves plain HTTP. Put it behind TLS (e.g.
  `tunnel.sh`) before exposing it publicly.
- The theme's webfonts load from Google Fonts on first paint; without network
  access the app still runs and falls back to `system-ui` / `Georgia`.
