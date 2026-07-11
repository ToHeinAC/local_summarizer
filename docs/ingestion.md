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
  adds Markdown structure **without changing any wording**.
- **Below the threshold** → the page is scanned/image-only. It is rasterized at
  `PDF_DPI` (default 150), JPEG-encoded, and sent to the vision `OCR_MODEL`.

Each page is classified independently, so mixed digital/scanned PDFs work. Pages
are joined with blank lines. Progress is reported per page via
`on_progress(done, total, label)`.

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
`temperature=0.0`.

## Cost note
The per-page rewrite means a digital PDF costs one LLM call per page *before*
summarization begins. This mirrors the reference repo. Set `REWRITE_MODEL` to a
fast model (e.g. `LiquidAI/lfm2.5-1.2b-instruct`) for large documents.

## Language detection (`src/language.py`)
`detect_language(text, fallback="en") -> str` returns an ISO-639-1 code via
`langdetect`. `DetectorFactory.seed = 0` makes it deterministic. Empty input or
detection failure returns `fallback`. Used to resolve the `auto` summary
language.
