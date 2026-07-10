# User Stories

## User
- As a user, I want to be able to upload a file and get a summary of its content, so that I can quickly understand the main points of the document.
- As a user, I want to be able to download the summary as a file in .md, .pdf and .docx formats, so that I can save it for later use.
- As a user, I want to see a progress bar while the summary is being generated, so that I know how long it will take.
- As a user, I want to be able to select the language of the summary (left side of the UI), so that I can get the summary in my preferred language (default: main language of the uploaded file).
- As a user, I want to be able to select a template for the summary from a predefined list of templates (left side of the UI), so that I can choose the information density and format of the summary.
- As a user, I want to be able to select from a predefined list of llm with their respective capabilities and performance metrics (left side of the UI), so that I can choose the best llm for my needs (for now: gemma4:e2b (fast) and gemma4:e4b (standard) -> default, qwen3:14b(smarter) and gpt-oss:20b (accurate); all from ollama)

## Development
- As a developer, I want to implement every feature using claude code (steps: catch feature (from developer and/or from an implementation plan), implement feature, test feature, document feature), so that I can deliver high-quality features quickly and efficiently.
- As a developer, I want the implementations to pass a test suite that covers the main functionality as well as edge cases (but in total not more than 200 tests; remove those already working consistently or merge tests that are testing similar things), so that I can ensure the quality of the code.
- As a developer, I want to document every feature I implement in a way that is easy to understand and maintain, so that I can ensure the code is maintainable and understandable.
- As a developer, I want to use a consistent coding style and follow best practices, so that I can ensure the code is maintainable.
- As a developer, I want to use a consistent project structure and organization, so that I can ensure the code is easy to navigate and understand.
- As a developer, I want to use a consistent naming convention for variables, functions, and files, so that I can ensure the code is easy to read and understand.
- As a developer, I want to use a consistent error handling strategy, so that I can ensure the code is robust and reliable.
- As a developer, I want to see the KISS (Keep It Simple, Stupid) principle applied to every feature I implement, so that I can ensure the code is simple and easy to understand.

## Acceptance Criteria
- All implementation must be under the Apache Licence 2.0 or more permissive (e.g. MIT).
- All implementation must be in python and the pythonic way of implementation.
- LangChain/LangGraph are permitted **only** inside the agent layer (e.g. `src/agent.py`, `src/tools.py`). Everywhere else: no LangChain, no vector DB, no embeddings, no cloud LLM APIs.
- `uv` is used for the virtual python environment setup and the running. Dependencies shall be defined in `pyproject.toml` and installed via `uv`.
- Use python-dotenv for the environmental variable handling.
- All domain Python modules live in `src/`. Run with `uv run streamlit run src/app.py --server.port 8530`.
  - Port **8530** is the project's chosen Streamlit port (avoids the default 8501 and a collision with another local app on 8520). Configurable via `APP_PORT` in `.env`.
- All LLM prompt strings must live in `src/prompts.py` as named module-level constants (e.g. `INGEST_PROMPT`). Never embed prompt strings inline in other modules.