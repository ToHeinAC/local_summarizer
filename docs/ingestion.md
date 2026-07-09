# Ingestion & language

## Extraction (`src/extract.py`)
`extract_text(filename, data) -> str` dispatches on the file extension:

| Extension | Library |
|---|---|
| `.pdf` | `pypdf` (concatenates per-page text) |
| `.docx` | `python-docx` (paragraph text) |
| `.txt`, `.md` | UTF-8 decode (`errors="replace"`) |

- Extension matching is case-insensitive.
- Output is whitespace-stripped.
- Unknown or missing extensions raise `UnsupportedFileError`.

## Language detection (`src/language.py`)
`detect_language(text, fallback="en") -> str` returns an ISO-639-1 code via
`langdetect`. `DetectorFactory.seed = 0` makes it deterministic. Empty input or
detection failure returns `fallback`. Used to resolve the `auto` summary
language.
