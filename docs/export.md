# Export

`src/export.py` renders a Markdown summary to downloadable bytes. It parses a
small Markdown subset shared with the templates: ATX headings (`#`..`######`)
and `-`/`*` bullet lists; any other non-blank line is a paragraph.

| Format | Function | Library |
|---|---|---|
| Markdown | `to_markdown` | UTF-8 encode |
| DOCX | `to_docx` | `python-docx` (headings, `List Bullet`, paragraphs) |
| PDF | `to_pdf` | `fpdf2` (pure Python) |

`EXPORTERS = {ext: (mime, fn)}` drives the UI download buttons.

## PDF fonts
`to_pdf` uses a system **DejaVu Sans** Unicode font when found (common Linux/mac
paths) so non-latin summaries render correctly. If none is found it falls back
to the built-in Helvetica and sanitizes text to latin-1, so generation never
crashes. Bundling a font would remove the fallback but add ~700 KB — deferred
until needed.
