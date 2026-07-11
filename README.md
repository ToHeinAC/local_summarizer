# Local Summarizer

Local, offline document summarizer. Upload a file, get a template-driven,
language-aware summary from a local Ollama LLM, and download it as `.md`,
`.pdf`, or `.docx`. No cloud APIs, no embeddings, no vector DB. **The UI is
German by default and toggles to English** with one sidebar button; the summary
language is chosen separately, per run (auto-detect by default).

## Features
Two steps, one tab each:

**1 · Umwandeln** (Convert) — upload **PDF, DOCX, TXT, MD**. The document is **converted to
Markdown first**; scanned PDF pages (no text layer) are **OCR'd locally** by an
Ollama vision model — no tesseract, no system binaries. Review the Markdown and
download it as `.md`.

**2 · Zusammenfassen** (Summarize) — summarize step 1's Markdown, or upload your own `.md`
(e.g. a corrected version). Pick **summary language** (auto-detect by default)
and **template**, then download the summary as **Markdown, PDF, or DOCX**.

Also: **sign-in** (bcrypt-hashed local user store), a **🌐 language toggle** and
a **model** picker in the sidebar, live **progress bar** (per page during
conversion), **Abmelden** (logout), and a safe in-app **App beenden** (exit)
button.

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

> **Note:** PDF pages that *do* have a text layer are reformatted as Markdown by
> one LLM call per page (`REWRITE_MODEL`, default `gemma4:e4b`). For long PDFs
> set `REWRITE_MODEL=LiquidAI/lfm2.5-1.2b-instruct` to keep it fast.

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
until port 8530 stops listening (or Ctrl-C). Requires
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
