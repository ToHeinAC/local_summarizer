# Agent layer

`src/agent.py` builds a LangGraph `StateGraph` over `SummaryState`. `src/tools.py`
wraps `ChatOllama`. All prompts are constants in `src/prompts.py`.

`make_llm` pins `num_ctx=tools.NUM_CTX` (8192). Without it Ollama allocates the
model's full trained window (128k for gemma4), which balloons the KV cache and
cuts throughput ~5×; every workload here (6000-char chunks, reduce batches of 8,
finalize) fits well under 8192, so the cap costs no precision.

## Nodes
1. **ingest** — `extract.to_markdown(..., fast=state["fast"])` converts file
   bytes to text (unless `text` is passed directly); `language.py` detects the
   source language. Raises `ValueError` on empty documents. Progress
   `0.0 → INGEST_SHARE` (0.40), driven per PDF page by the converter.
   See [ingestion.md](ingestion.md).
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
    fast=False,                                # True: verbatim text, skip rewrite
    on_progress=lambda frac, label: ...,
    ui_lang="de",                              # language of the progress labels
    return_markdown=False,                     # True: also return converted Markdown
) -> str  # Markdown summary (or (summary, converted_markdown) if return_markdown)
```
`model_id` is resolved to an Ollama tag via `models.get_model`. `ocr_model` and
`rewrite_model` are raw Ollama tags, not registry ids. `fast` travels in
`SummaryState["fast"]` and `_ingest` forwards it to `extract.to_markdown(fast=...)`:
with `fast=True` (what the UI passes) digital PDF pages use their text layer
verbatim and `rewrite_model` goes unused; scanned pages still OCR. See
[ingestion.md](ingestion.md). `ui_lang` (`"de"`/`"en"`) only selects the language
of the progress labels, which the nodes build with `i18n.t`; the summary's own
language is `target_language`. It travels in `SummaryState["ui_lang"]` and is
forwarded to `extract.to_markdown(lang=...)`.

`return_markdown=True` returns a `(summary, converted_markdown)` tuple instead of
just the summary; the second item is `SummaryState["text"]`, i.e. the text the
document was converted to before summarizing (the LLM-rewritten Markdown when
`fast=False`). The UI uses this in the precise mode to offer the generated
document Markdown as its own download.

## Testing hook
Nodes call `make_llm`/`run_prompt` from the module namespace, so tests
monkeypatch `agent.make_llm` and `agent.run_prompt` to run fully offline
(`tests/test_agent.py`). Conversion is stubbed separately via the `stub_ollama`
fixture, which patches `ollama_client.ocr/rewrite/unload`.
