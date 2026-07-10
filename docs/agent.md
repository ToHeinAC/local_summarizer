# Agent layer

`src/agent.py` builds a LangGraph `StateGraph` over `SummaryState`. `src/tools.py`
wraps `ChatOllama`. All prompts are constants in `src/prompts.py`.

## Nodes
1. **ingest** — `extract.to_markdown()` converts file bytes to Markdown (unless
   `text` is passed directly); `language.py` detects the source language. Raises
   `ValueError` on empty documents. Progress `0.0 → INGEST_SHARE` (0.40), driven
   per PDF page by the converter. See [ingestion.md](ingestion.md).
2. **chunk** — `split_text()` splits into overlapping character chunks
   (`CHUNK_SIZE=6000`, `CHUNK_OVERLAP=200`). Progress 0.42.
3. **map** — summarizes each chunk with `MAP_PROMPT`. Single-chunk documents
   skip the LLM here and pass the chunk straight through. Progress 0.42→0.80.
4. **reduce** — only when >1 partial summary. Combines with `REDUCE_PROMPT`
   hierarchically in batches of `REDUCE_BATCH=8` until one summary remains,
   so very large documents stay within context. Progress 0.85.
5. **finalize** — applies the chosen template `structure` and target language
   via `FINALIZE_PROMPT`, producing the final Markdown. Progress 0.90→1.0.

Edges: `ingest→chunk→map`, then conditional `map→reduce|finalize`,
`reduce→finalize`, `finalize→END`.

`INGEST_SHARE` is the conversion's slice of the progress bar. Conversion is now
the dominant cost for PDFs (one LLM call per page), which is why it gets 40%.

## Language resolution
`target_language="auto"` uses the detected source language; otherwise the
selected code is used. Codes map to names via `prompts.LANGUAGE_LABELS`
(unknown codes pass through as-is). Detection runs on the **converted Markdown**.

## Entry point
```python
agent.run(
    template_id="standard", model_id="standard",
    filename="report.pdf", data=pdf_bytes,     # or text="..."
    target_language="auto", host="http://localhost:11434",
    ocr_model="deepseek-ocr:3b",               # vision model for scanned pages
    rewrite_model="gemma4:e4b",                # text model for digital pages
    pdf_dpi=150,
    on_progress=lambda frac, label: ...,
    ui_lang="de",                              # language of the progress labels
) -> str  # Markdown
```
`model_id` is resolved to an Ollama tag via `models.get_model`. `ocr_model` and
`rewrite_model` are raw Ollama tags, not registry ids. `ui_lang` (`"de"`/`"en"`)
only selects the language of the progress labels, which the nodes build with
`i18n.t`; the summary's own language is `target_language`. It travels in
`SummaryState["ui_lang"]` and is forwarded to `extract.to_markdown(lang=...)`.

## Testing hook
Nodes call `make_llm`/`run_prompt` from the module namespace, so tests
monkeypatch `agent.make_llm` and `agent.run_prompt` to run fully offline
(`tests/test_agent.py`). Conversion is stubbed separately via the `stub_ollama`
fixture, which patches `ollama_client.ocr/rewrite/unload`.
