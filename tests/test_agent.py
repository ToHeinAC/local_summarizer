import pytest

from src import agent


@pytest.fixture
def recorder(monkeypatch):
    """Capture prompts sent to the LLM; return a canned response."""
    prompts: list[str] = []

    def fake_run_prompt(llm, prompt):
        prompts.append(prompt)
        return f"OUT{len(prompts)}"

    monkeypatch.setattr(agent, "make_llm", lambda *a, **k: object())
    monkeypatch.setattr(agent, "unload", lambda *a, **k: None)
    monkeypatch.setattr(agent, "run_prompt", fake_run_prompt)
    return prompts


def test_split_text_single_chunk():
    assert agent.split_text("short text") == ["short text"]


def test_split_text_multiple_chunks():
    chunks = agent.split_text("A" * 15000)
    assert len(chunks) > 1
    assert all(len(c) <= agent.CHUNK_SIZE for c in chunks)


def test_run_short_text_single_pass(recorder):
    summary = agent.run(text="A short document.", template_id="standard", model_id="fast")
    # Single chunk => map is a no-op, reduce skipped, one finalize call.
    assert len(recorder) == 1
    assert summary == "OUT1"


def test_run_return_markdown_yields_summary_and_converted_text(recorder):
    summary, markdown = agent.run(
        text="A short document.",
        template_id="standard",
        model_id="fast",
        return_markdown=True,
    )
    assert summary == "OUT1"
    assert markdown == "A short document."  # the text it was converted to


def test_run_long_text_triggers_map_and_reduce(recorder):
    summary = agent.run(text="A" * 15000, template_id="standard", model_id="fast")
    # 3 map calls + 1 reduce + 1 finalize.
    assert len(recorder) == 5
    assert summary.startswith("OUT")


def test_empty_text_raises(recorder):
    with pytest.raises(ValueError):
        agent.run(text="   ", template_id="standard", model_id="fast")


def test_progress_reaches_completion(recorder):
    events: list[tuple[float, str]] = []
    agent.run(
        text="A short document.",
        template_id="standard",
        model_id="fast",
        on_progress=lambda frac, label: events.append((frac, label)),
    )
    fractions = [f for f, _ in events]
    assert fractions == sorted(fractions)
    assert fractions[-1] == 1.0


def test_progress_never_decreases_through_pdf_conversion(recorder, pdf_bytes, stub_ollama):
    events: list[float] = []
    agent.run(
        filename="report.pdf",
        data=pdf_bytes,
        template_id="standard",
        model_id="fast",
        on_progress=lambda frac, label: events.append(frac),
    )
    assert events == sorted(events), f"progress bar ran backwards: {events}"
    assert events[-1] == 1.0


def test_pdf_is_converted_to_markdown_before_summarizing(recorder, pdf_bytes, stub_ollama):
    agent.run(filename="report.pdf", data=pdf_bytes, template_id="standard", model_id="fast")
    assert stub_ollama.rewritten, "the PDF must be converted to Markdown first"
    # The finalize prompt receives the converted Markdown, not the raw text layer.
    assert "# Rewritten" in recorder[-1]


def test_fast_pdf_skips_the_per_page_rewrite(recorder, pdf_bytes, stub_ollama):
    """fast=True uses the digital page's text layer verbatim: no rewrite call."""
    agent.run(
        filename="report.pdf",
        data=pdf_bytes,
        template_id="standard",
        model_id="fast",
        fast=True,
    )
    assert not stub_ollama.rewritten, "fast mode must not LLM-rewrite digital pages"


def test_explicit_target_language_in_finalize_prompt(recorder):
    agent.run(text="A short document.", template_id="standard", model_id="fast", target_language="de")
    assert "German" in recorder[-1]


def test_auto_language_detected_for_finalize(recorder):
    agent.run(
        text="This is clearly written in the English language for testing.",
        template_id="standard",
        model_id="fast",
    )
    assert "English" in recorder[-1]


def test_hybrid_uses_small_model_for_chunks_and_big_for_final(monkeypatch):
    built: list[str] = []
    llms: dict[str, object] = {}

    def fake_make_llm(tag, host=None):
        built.append(tag)
        return llms.setdefault(tag, type("L", (), {"tag": tag})())

    used: list[tuple[str, str]] = []
    unloaded: list[str] = []
    monkeypatch.setattr(agent, "make_llm", fake_make_llm)
    monkeypatch.setattr(agent, "run_prompt", lambda llm, p: (used.append((llm.tag, p)), "X")[1])
    monkeypatch.setattr(agent, "unload", lambda tag, host=None: unloaded.append(tag))

    agent.run(text="A" * 15000, template_id="standard", model_id="hybrid")
    tags = [tag for tag, _ in used]
    # 3 map + 1 reduce on the small model, then one finalize on the big one.
    assert tags == ["gemma4:e4b"] * 4 + ["qwen3.8-27b:latest"]
    assert unloaded == ["gemma4:e4b"]


def test_hybrid_single_chunk_goes_straight_to_big_model(monkeypatch):
    used: list[str] = []
    unloaded: list[str] = []
    monkeypatch.setattr(agent, "make_llm", lambda tag, host=None: tag)
    monkeypatch.setattr(agent, "run_prompt", lambda llm, p: (used.append(llm), "X")[1])
    monkeypatch.setattr(agent, "unload", lambda tag, host=None: unloaded.append(tag))
    agent.run(text="Short.", template_id="standard", model_id="hybrid")
    assert used == ["qwen3.8-27b:latest"]
    assert unloaded == []
