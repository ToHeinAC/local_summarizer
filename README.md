# Local Summarizer

Local, offline document summarizer. Upload a file, get a template-driven,
language-aware summary from a local Ollama LLM, and download it as `.md`,
`.pdf`, or `.docx`. No cloud APIs, no embeddings, no vector DB. **The UI is
German by default and toggles to English** with one sidebar button; the summary
language is chosen separately, per run (auto-detect by default).

## Features
One window, one click. In the main panel pick the **model** and a **precision**
mode (*Schnellmodus* — fast/verbatim, the default — or *Genaues Markdown* —
precise, LLM-formatted), the **summary language** (auto-detect by default) and
**template**, upload a **PDF, DOCX, TXT, or MD** file, and press
**Zusammenfassen** (Summarize). That single click:

1. **converts** the document to text — by default digital PDF pages are used
   verbatim (near-instant, byte-exact) and scanned pages (no text layer) are
   **OCR'd locally** by an Ollama vision model (no tesseract, no system
   binaries); the *precise* option instead LLM-formats each text page; then
2. **summarizes** it with the chosen local LLM.

The summary is shown and downloadable as **Markdown, PDF, or DOCX**. There is no
separate convert step and no intermediate Markdown to manage.

Also: **sign-in** (bcrypt-hashed local user store), a **🌐 language toggle** in
the sidebar, and a live **progress bar** across the whole run. **Abmelden**
(logout) clears the session but leaves the app — and any live tunnel — running;
there is no in-app exit button, so stop the server from the terminal
(`./tunnel.sh stop`) to avoid tearing a tunnel down unexpectedly.

## Requirements
- Python ≥ 3.12, [`uv`](https://docs.astral.sh/uv/), and [Ollama](https://ollama.com).
- Pull at least the default summarization model:
  ```bash
  ollama pull gemma4:e4b        # standard (default)
  ollama pull LiquidAI/lfm2.5-1.2b-instruct   # fast
  ollama pull qwen3:14b         # smarter
  ollama pull gpt-oss:20b       # accurate
  ```
  The UI greys out and warns about any model that is not installed.
- To summarize **PDFs**, also pull the OCR model:
  ```bash
  ollama pull deepseek-ocr:3b   # reads scanned pages
  ```

> **Note:** by default the UI reads digital PDF pages verbatim (no LLM call per
> page), so only scanned pages need the OCR model. The per-page Markdown rewrite
> (`REWRITE_MODEL`, default `gemma4:e4b`) runs only for the *precise* option (and
> direct API callers) via `agent.run(fast=False)`.

## Setup & run
```bash
uv sync
cp .env.example .env            # optional: adjust OLLAMA_HOST / defaults
uv run streamlit run src/app.py --server.port 8530
```

## Sign-in
The app requires a login. Set the seed passwords in `.env` before the first run:

```bash
SEED_PW_HEIN=...        # account "T. Hein"
SEED_PW_GAST=...        # account "Gast"
```

On first run `data/users.json` is created from them. Only bcrypt hashes are
stored, and both `.env` and `data/` are gitignored — no credential ever reaches
the repo. To change a password, update `.env` and delete `data/users.json` so it
is re-seeded; to change the accounts themselves, edit `auth.SEED_USERS`.

## Remote access (Cloudflare quick tunnel)
```bash
./tunnel.sh
```
Starts the app if it isn't running, then opens a temporary `*.trycloudflare.com`
public URL for port 8530 — no Cloudflare account required. The tunnel stays up
until port 8530 stops listening; run `./tunnel.sh stop` to shut down both the app
and the tunnel. Requires
[`cloudflared`](https://developers.cloudflare.com/cloudflare-one/connections/connect-networks/downloads/).

## Tests
```bash
uv run pytest
```

## Documentation
- [IMPLEMENTATION.md](IMPLEMENTATION.md) — current state and module map.
- [docs/](docs/) — per-component detail.
- [PRD.md](PRD.md) — original goals. [AGENTS.md](AGENTS.md) — collaboration rules.

## License
Apache-2.0. See [LICENSE](LICENSE).
