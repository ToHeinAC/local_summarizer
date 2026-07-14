# CLAUDE.md

The shared, vendor-neutral collaboration rules for AI coding tools live in [AGENTS.md](AGENTS.md) (also read by Codex, Cursor, etc.). Claude Code reads *this* file, so the import below pulls in the shared rules — one source of truth for every tool.

@AGENTS.md

## Project at a glance
Local, offline document summarizer: Streamlit UI → Markdown conversion (vision OCR for scanned PDFs) → LangGraph map-reduce agent → local Ollama LLM → Markdown summary downloadable as `.md` / `.pdf` / `.docx`. No cloud *LLM* APIs, no embeddings, no vector DB. A second sidebar section (**📈 Portfolio**, phase 4) tracks a self-chosen stock portfolio — plain Python, no LLM — with 100-bagger, hold-biased recommendations; its only network touch is `yfinance` for live quotes (market data, not an LLM API), which degrades to manual entry offline. See [docs/portfolio.md](docs/portfolio.md).

```bash
uv sync
uv run streamlit run src/app.py --server.port 8530   # port per PRD.md
uv run pytest                                        # 139 tests, fully offline
```

**Hard boundary:** LangChain/LangGraph may be imported *only* by `src/agent.py` and `src/tools.py`. Every other module is plain Python — `src/ollama_client.py` reaches Ollama through the plain `ollama` package, and `src/prices.py` reaches Yahoo Finance through `yfinance`; neither is LangChain, so both are fine. All prompt strings are named constants in `src/prompts.py`.

## Documentation map
Start with [IMPLEMENTATION.md](IMPLEMENTATION.md) @IMPLEMENTATION.md — current state, module map, key decisions. Deep detail per component:

- [docs/architecture.md](docs/architecture.md) @docs/architecture.md — layers, data flow, progress callback, configuration
- [docs/agent.md](docs/agent.md) @docs/agent.md — LangGraph nodes, `SummaryState`, chunking/reduce constants, `agent.run()` entry point, test hooks
- [docs/ingestion.md](docs/ingestion.md) @docs/ingestion.md — Markdown-first conversion, per-page PDF rewrite/OCR routing, language detection
- [docs/ui.md](docs/ui.md) @docs/ui.md — Forest palette, fonts, CSS injection, layout conventions
- [docs/models.md](docs/models.md) @docs/models.md — Ollama model registry, availability check
- [docs/templates.md](docs/templates.md) @docs/templates.md — summary template registry, how to add one
- [docs/export.md](docs/export.md) @docs/export.md — md/pdf/docx rendering, PDF font fallback
- [docs/portfolio.md](docs/portfolio.md) @docs/portfolio.md — stock portfolio: CSV round-trip, yfinance/manual prices, 100-bagger rules
- [docs/testing.md](docs/testing.md) @docs/testing.md — test map and fixtures

[PRD.md](PRD.md) holds the original goals and acceptance criteria.

## Claude Code specifics
- Slash commands: `.claude/commands/` (`commit-git`, `create-prd`, `documentation-update`). Skills: `.claude/skills/` (`code_review`).
- Permissions/config: shared safe allows are committed in `.claude/settings.json`; machine-personal ones stay in `.claude/settings.local.json` (gitignored).
