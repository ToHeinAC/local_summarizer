# Ingestion & language

Every upload becomes **Markdown before summarization**. Pipeline ported from
[ToHeinAC/KB_BS_local-wiki-he](https://github.com/ToHeinAC/KB_BS_local-wiki-he)
(Apache-2.0), itself derived from `ToHeinAC/MD-maker`.

## Dispatch (`src/extract.py`)
`to_markdown(filename, data, *, ocr_model, rewrite_model, dpi, host, on_progress, lang) -> str`
dispatches on the file extension (`lang` only selects the language of the
progress labels and of `UnsupportedFileError`; default `"de"`):

| Extension | Path |
|---|---|
| `.pdf` | per-page routing via `md_convert.pdf_to_markdown` (see below) |
| `.docx` | `md_convert.docx_to_markdown` — deterministic, no LLM |
| `.txt`, `.md` | UTF-8 decode (`errors="replace"`), already text |

- Extension matching is case-insensitive; output is whitespace-stripped.
- Unknown or missing extensions raise `UnsupportedFileError`.

## PDF: per-page routing (`src/md_convert.py`)
`iter_pdf_pages` uses `pypdfium2` to read each page's text layer:

- **`len(text) >= TEXT_THRESHOLD` (40 chars)** → the page has a usable text
  layer. Its text is sent to `REWRITE_MODEL` with `MD_REWRITE_PROMPT`, which
  adds Markdown structure **without changing any wording** — unless `fast=True`
  (the UI default), which uses the extracted text verbatim (see Fast mode below).
- **Below the threshold** → the page is scanned/image-only. It is rasterized at
  `PDF_DPI` (default 150), JPEG-encoded, and sent to the vision `OCR_MODEL`.

Each page is classified independently, so mixed digital/scanned PDFs work. Pages
are converted concurrently through a `ThreadPoolExecutor`
(`MAX_CONVERT_WORKERS = 4` LLM calls in flight) — each page is an independent
Ollama request and the per-page rewrite/OCR dominates conversion time. Rendering
stays on the calling thread (pypdfium2 is not thread-safe); only the LLM calls
run in the pool. Results are slotted back by page index so output order is
preserved, and progress counts *completed* pages so the bar stays monotonic
despite out-of-order completion. Pages are joined with blank lines; progress is
reported per completed page via `on_progress(done, total, label)`.

**Server-side parallelism required.** The client sends up to `MAX_CONVERT_WORKERS`
requests at once, but Ollama only runs them concurrently when its server allows
≥2 slots. Set `OLLAMA_NUM_PARALLEL=4` on the Ollama server (systemd override or
env) — with the default (1 slot here) the requests queue and the speedup is
negligible. Measured ~1.9× on a 6-page digital PDF once enabled.

**OCR prompt selection:** `deepseek-ocr*` models get `OCR_DEEPSEEK_PROMPT`
(the `<|grounding|>` token enables layout-aware OCR); any other vision model gets
`OCR_SYSTEM_PROMPT` + `OCR_USER_PROMPT`.

**VRAM:** after a PDF that actually used OCR, the vision model is evicted
(`ollama_client.unload`, `keep_alive=0`) so the summarizer's text model gets the
full GPU. Skipped when no page was OCR'd — otherwise the model would be loaded
just to be evicted.

## DOCX → Markdown
Walks the document body in order, mapping `Heading 1..3` → `#`/`##`/`###`,
bullet/number styles → `-`/`1.`, and tables → Markdown tables. No LLM call.

## Ollama access (`src/ollama_client.py`)
Plain `ollama` package (not LangChain), so the ingestion layer stays inside the
project's LangChain boundary. Exposes `ocr()`, `rewrite()`, `unload()`, all at
`temperature=0.0`. Both `ocr` and `rewrite` pin `num_ctx` (`REWRITE_NUM_CTX=8192`,
`OCR_NUM_CTX=16384`): without it Ollama allocates each model's full trained
window (128k for gemma4), which balloons VRAM and cuts throughput ~5×. One page
of text (or its image tokens) fits comfortably, so the cap costs no precision.

## Fast mode (the UI default)
`pdf_to_markdown(..., fast=True)` (and `to_markdown(..., fast=True)`) skips the
rewrite entirely for pages that already have a text layer: the pypdfium2-extracted
text is used verbatim, so a digital PDF converts with **zero** LLM calls (measured
32s → ~0s for a 6-page PDF) and byte-exact wording. Scanned pages still OCR.
Trade-off: no LLM-added headings/tables and raw reading order on multi-column
layouts.

**The UI defaults to `fast=True`** — `agent.run(fast=True)` →
`to_markdown(fast=True)` — trading the per-page rewrite's tidier Markdown for a
near-instant, byte-exact conversion. A main-panel selectbox (*Schnellmodus
(wörtlich)* by default, or *Genaues Markdown (LLM)*) flips it to `fast=False` for
callers who want the LLM-formatted pass; see [ui.md](ui.md).

## Cost note (`fast=False`)
With `fast=False` (the UI's precise option, or direct API callers) the per-page
rewrite means a digital PDF costs one LLM call per page *before* summarization
begins — this mirrors the reference repo. The calls run concurrently (see above),
so wall-clock cost is roughly the per-page cost times `ceil(pages / effective_slots)`.
Set `REWRITE_MODEL` to a fast model (e.g. `LiquidAI/lfm2.5-1.2b-instruct`) for
large documents.

## Language detection (`src/language.py`)
`detect_language(text, fallback="en") -> str` returns an ISO-639-1 code via
`langdetect`. `DetectorFactory.seed = 0` makes it deterministic. Empty input or
detection failure returns `fallback`. Used to resolve the `auto` summary
language.
