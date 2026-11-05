# Agent layer

`src/agent.py` builds a LangGraph `StateGraph` over `SummaryState`. `src/tools.py`
wraps `ChatOllama`. All prompts are constants in `src/prompts.py`.

## Context window and prompt budget
`make_llm` sets `num_ctx=models.num_ctx(tag)` — a per-model window measured to
keep the model 100 % on one 24 GB RTX 4090 (see [models.md](models.md)) — and
`num_predict=tools.NUM_PREDICT` (6144) as a guard against runaway repetition.
gemma4:e4b gets the full **131072** tokens: its sliding-window attention keeps
that at ~7 GB VRAM in total. The earlier blanket `num_ctx=8192` fixed a real
slowdown (128k × `NUM_PARALLEL=4` on the shared daemon spilling across both
GPUs) but forced 6000-char chunks; on the pinned single-slot daemon a large
window costs only VRAM, and prefill runs at ~8–13k tokens/s.

How much source text goes into one prompt is `agent.input_chars(tag)`:

```
min( (num_ctx - RESERVED_TOKENS) * MIN_CHARS_PER_TOKEN ,   # never truncated
     MAX_INPUT_TOKENS * CHARS_PER_TOKEN )                  # quality cap
```

- `RESERVED_TOKENS = NUM_PREDICT + 2048` — prompt text, overview, answer.
- `MIN_CHARS_PER_TOKEN = 2.5` guards the hard limit. **Ollama silently drops
  the start of a prompt that exceeds `num_ctx`** (measured: a 128k-token
  prompt came back as 65k evaluated tokens, no error), so this side must be
  worst-case.
- `MAX_INPUT_TOKENS = 32768` at `CHARS_PER_TOKEN = 3.3` (typical, measured
  3.0–3.5 on German reports) ≈ 108k chars ≈ 30 pages. This is the quality
  side: see *Why cap at 32k* below.

## Nodes
1. **ingest** — `extract.to_markdown(..., fast=state["fast"])` converts file
   bytes to text (unless `text` is passed directly); `language.py` detects the
   source language. Raises `ValueError` on empty documents. Progress
   `0.0 → INGEST_SHARE` (0.40), driven per PDF page by the converter.
   See [ingestion.md](ingestion.md).
2. **chunk** — if the whole text fits `input_chars(final model)` it stays one
   part (**single pass**: the template sees the original document). Otherwise
   `split_text()` cuts the fewest *balanced* parts of at most
   `input_chars(map model)`, overlapping by `CHUNK_OVERLAP=1000` chars and ending
   on a line break. Progress 0.42.
3. **map** — single part: pass-through, no LLM call. Several parts: first one
   `BRIEF_PROMPT` call on the opening `BRIEF_CHARS=20000` chars (title page,
   table of contents, introduction) yields a ≤200-word **document overview**;
   then each part gets `MAP_PROMPT` with that overview and its position
   ("part 2 of 5"). The answer is structured **notes**, not prose, under fixed
   headings (Objective and scope / Method and data / Results / Conclusions /
   Recommendations and measures / Referenced documents) — exactly what the four
   templates draw on. Uses `map_model_tag` for the hybrid (see
   [models.md](models.md)). Progress 0.43→0.80.
4. **reduce** — only when the joined notes exceed `input_chars(final model)`;
   merges them with `REDUCE_PROMPT` in batches of `REDUCE_BATCH=8` until they
   fit. With a 128k window this practically never runs (5 parts of notes ≈
   60k chars). Progress 0.85.
5. **finalize** — `FINALIZE_PROMPT` with the template `structure`, the target
   language, the overview (multi-part only) and either the full document or all
   notes. Progress 0.90→1.0.

### Prompt rules and why each exists
- **Notes stay in the source language** (`MAP_PROMPT`, `REDUCE_PROMPT`). The old
  map prompt said nothing about language; gemma wrote English notes on a German
  report, and the German summary then carried back-translation errors
  ("Flussbettenverstärkung" for *Bachsohlenbefestigung*, "Lead-210").
- **Source anchors verbatim** (`_ANCHORS`): quantities with units, § / clause
  numbers, figure/table/appendix ids, cited documents, names, dates. Finalize
  only sees the notes, so an anchor dropped there cannot be cited.
- **No concrete example identifiers in any prompt or template.** With examples
  like "DIN 25457", "[BS 04]", gemma4:e4b listed exactly those as references of
  an EPA report that cites none of them, then looped on the list until
  `num_predict`. Examples name a category only; a test guards this.
- **Plain text, no LaTeX, no bold** (`_PLAIN`): gemma otherwise writes
  `$\text{Ra-226}$`, which the md/docx/pdf exporters print literally.
- **Headings only in the target language**: otherwise "Zielsetzung (Objective)".
- `temperature=0.2`: at gemma's default 1.0 map notes had up to 6 duplicate
  lines and 90 `$` signs per part; at 0.2 with the "never repeat" rule 0–1 and
  0–2. `repeat_penalty=1.1` made no difference and is not set.

### Why cap at 32k tokens per part (not the full 128k)
The window allows ~300k chars per prompt, yet parts are capped at ~108k chars.
The bottleneck is the **answer**, not the input: one call writes a few thousand
tokens of notes at most, so a big part is compressed far harder before
finalize ever sees it. Measured on the 184-page StrlSchV (200 §§), notes only:

| Parts | Notes reaching finalize | distinct §§ cited in notes |
|---|---|---|
| 2 × ~80k tokens (`MAX_INPUT_TOKENS=120000`) | 12k chars | 49 / 200 |
| 6 × ~25k tokens (`MAX_INPUT_TOKENS=32768`) | 94k chars | 113 / 200 |

32k is also about the largest cap where a 180-page document's notes still fit
one finalize prompt, so reduce stays unused. Retrieval is not the limit — a
needle test found three planted facts at 10/50/90 % depth of a 100k-token
prompt — but needle recall overstates what a 4B model can *condense* in one
answer.

### Measured effect (gemma4:e4b, pinned RTX 4090, `fast=True`)
| Document | Old pipeline | New pipeline |
|---|---|---|
| 1509-09 Endbericht, 43 p., 66k chars | 16 calls, 155 s | 1 call (single pass), 5–19 s |
| EPA 402-R-04-002C, 188 p., 445k chars | — | overview + 5 parts + final, 1.5–2.7 min |
| StrlSchV, 184 p., 539k chars | ~95 calls, ~15 min | overview + 6 parts + final, ~3 min |

Lengths land near the targets (executive 226–254, bullets 432, action items
430–474, detailed 1000–1100 words). Every figure spot-checked in the 1509-09
summaries matched the source; the one error was an attribution (a mean value
assigned to the wrong stream). Remaining limit: a 2-page summary of a 180-page
document must select — the EPA `detailed` run gave 5 of its 7 elements their
own subsection.

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
    rewrite_model="gemma3:4b",                 # small text model for digital pages
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
Multi-part paths are exercised by shrinking the budget: the `small_budget`
fixture monkeypatches `agent.input_chars` to 6000 chars, so a 15000-char text
splits into three parts without needing a 300k-char fixture.
