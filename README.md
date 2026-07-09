# Local Summarizer

Local, offline document summarizer. Upload a file, get a template-driven,
language-aware summary from a local Ollama LLM, and download it as `.md`,
`.pdf`, or `.docx`. No cloud APIs, no embeddings, no vector DB.

## Features
- Upload **PDF, DOCX, TXT, MD**.
- Every document is **converted to Markdown first**. Scanned PDF pages (no text
  layer) are **OCR'd locally** by an Ollama vision model — no tesseract, no
  system binaries.
- Pick **summary language** (auto-detect by default), **template**, and **model**.
- Live **progress bar**, per page during conversion.
- Download the summary as **Markdown, PDF, or DOCX**.
- Safe in-app **exit button**.

## Requirements
- Python ≥ 3.12, [`uv`](https://docs.astral.sh/uv/), and [Ollama](https://ollama.com).
- Pull at least the default summarization model:
  ```bash
  ollama pull gemma4:e4b        # standard (default)
  ollama pull gemma4:e2b        # fast
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
> set `REWRITE_MODEL=gemma4:e2b` to keep it fast.

## Setup & run
```bash
uv sync
cp .env.example .env            # optional: adjust OLLAMA_HOST / defaults
uv run streamlit run src/app.py --server.port 8506
```

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
