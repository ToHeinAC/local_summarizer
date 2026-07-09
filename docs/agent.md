# Agent layer

`src/agent.py` builds a LangGraph `StateGraph` over `SummaryState`. `src/tools.py`
wraps `ChatOllama`. All prompts are constants in `src/prompts.py`.

## Nodes
1. **ingest** — `extract.py` turns file bytes into text (unless `text` is passed
   directly); `language.py` detects the source language. Raises `ValueError`
   on empty documents. Progress 0.05.
2. **chunk** — `split_text()` splits into overlapping character chunks
   (`CHUNK_SIZE=6000`, `CHUNK_OVERLAP=200`). Progress 0.10.
3. **map** — summarizes each chunk with `MAP_PROMPT`. Single-chunk documents
   skip the LLM here and pass the chunk straight through. Progress 0.10→0.75.
4. **reduce** — only when >1 partial summary. Combines with `REDUCE_PROMPT`
   hierarchically in batches of `REDUCE_BATCH=8` until one summary remains,
   so very large documents stay within context. Progress 0.80.
5. **finalize** — applies the chosen template `structure` and target language
   via `FINALIZE_PROMPT`, producing the final Markdown. Progress 0.90→1.0.

Edges: `ingest→chunk→map`, then conditional `map→reduce|finalize`,
`reduce→finalize`, `finalize→END`.

## Language resolution
`target_language="auto"` uses the detected source language; otherwise the
selected code is used. Codes map to names via `prompts.LANGUAGE_LABELS`
(unknown codes pass through as-is).

## Entry point
```python
agent.run(
    template_id="standard", model_id="standard",
    filename="report.pdf", data=pdf_bytes,     # or text="..."
    target_language="auto", host="http://localhost:11434",
    on_progress=lambda frac, label: ...,
) -> str  # Markdown
```
`model_id` is resolved to an Ollama tag via `models.get_model`.

## Testing hook
Nodes call `make_llm`/`run_prompt` from the module namespace, so tests
monkeypatch `agent.make_llm` and `agent.run_prompt` to run fully offline
(`tests/test_agent.py`).
