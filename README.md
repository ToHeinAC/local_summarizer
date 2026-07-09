# Local Summarizer

Local, offline document summarizer. Upload a file, get a template-driven,
language-aware summary from a local Ollama LLM, and download it as `.md`,
`.pdf`, or `.docx`. No cloud APIs, no embeddings, no vector DB.

## Features
- Upload **PDF, DOCX, TXT, MD**.
- Pick **summary language** (auto-detect by default), **template**, and **model**.
- Live **progress bar** during summarization.
- Download the summary as **Markdown, PDF, or DOCX**.
- Safe in-app **exit button**.

## Requirements
- Python ≥ 3.12, [`uv`](https://docs.astral.sh/uv/), and [Ollama](https://ollama.com).
- Pull at least the default model:
  ```bash
  ollama pull gemma4:e4b        # standard (default)
  ollama pull gemma4:e2b        # fast
  ollama pull qwen3:14b         # smarter
  ollama pull gpt-oss:20b       # accurate
  ```
  The UI greys out and warns about any model that is not installed.

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
