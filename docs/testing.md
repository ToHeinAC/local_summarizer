# Testing

Run: `uv run pytest`. Tests are fully offline — the LLM is monkeypatched, so no
Ollama server is required. 46 tests total (well under the 200 cap).

| File | Covers |
|---|---|
| `test_config.py` | defaults + env overrides |
| `test_prompts.py` | prompt constants and their `{}` slots |
| `test_extract.py` | pdf/docx/txt/md extraction, unsupported/no extension, stripping |
| `test_language.py` | English/German detection, fallbacks |
| `test_models.py` | registry shape, default, availability annotation, unreachable server |
| `test_templates.py` | registry shape, default, unknown id |
| `test_agent.py` | chunk split, single-pass vs map-reduce, progress, language resolution, empty input |
| `test_export.py` | md/docx/pdf output validity, unicode, exporters registry |
| `test_app.py` | UI helpers, accepted formats, config wiring |

## Fixtures (`conftest.py`)
In-memory sample documents (`txt_bytes`, `md_bytes`, `docx_bytes`, `pdf_bytes`)
and a `FakeLLM`. Edge cases covered: empty document, unsupported/no extension,
multi-chunk map-reduce, undetectable language, unreachable Ollama, unicode PDF.
