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


@pytest.fixture
def small_budget(monkeypatch):
    """Shrink every model's input budget so 15000 chars need three chunks."""
    monkeypatch.setattr(agent, "input_chars", lambda tag: 6000)


def test_split_text_single_chunk():
    assert agent.split_text("short text", size=100) == ["short text"]


def test_split_text_balanced_chunks_cover_everything():
    text = "".join(f"line {i:05d}\n" for i in range(1500))  # 16500 chars
    chunks = agent.split_text(text, size=6000, overlap=500)
    assert len(chunks) == 3
    assert all(len(c) <= 6000 for c in chunks)
    # Balanced: no tiny tail chunk left over.
    assert min(len(c) for c in chunks) > 0.6 * max(len(c) for c in chunks)
    # Cuts land on line boundaries, and nothing is lost between chunks.
    assert all(c.endswith("\n") for c in chunks[:-1])
    for i in range(1500):
        assert any(f"line {i:05d}" in c for c in chunks)


def test_input_chars_follows_the_model_window(monkeypatch):
    monkeypatch.setattr(agent, "MAX_INPUT_TOKENS", 10**9)
    small = agent.input_chars("LiquidAI/lfm2.5-1.2b-instruct:latest")  # 32k window
    large = agent.input_chars("gemma4:e4b")  # 128k window
    assert large > 3 * small
    assert small > 0


def test_run_short_text_single_pass(recorder):
    summary = agent.run(text="A short document.", template_id="bullets", model_id="fast")
    # Single chunk => map is a no-op, reduce skipped, one finalize call.
    assert len(recorder) == 1
    assert summary == "OUT1"


def test_run_return_markdown_yields_summary_and_converted_text(recorder):
    summary, markdown = agent.run(
        text="A short document.",
        template_id="bullets",
        model_id="fast",
        return_markdown=True,
    )
    assert summary == "OUT1"
    assert markdown == "A short document."  # the text it was converted to


def test_whole_document_in_one_prompt_when_it_fits(recorder):
    text = "Kapitel 1. " * 2000  # 22000 chars: far below gemma4's window
    agent.run(text=text, template_id="bullets", model_id="standard")
    assert len(recorder) == 1, "a document that fits the window needs no map pass"
    assert text.strip() in recorder[0]
    assert "NOTES ON PART" not in recorder[0]


def test_long_text_gets_overview_then_notes_then_final(recorder, small_budget):
    summary = agent.run(text="A" * 15000, template_id="bullets", model_id="fast")
    # 1 overview + 3 map notes + 1 finalize; the short notes need no reduce.
    assert len(recorder) == 5
    brief, *maps, final = recorder
    assert "opening pages" in brief.lower()
    for i, prompt in enumerate(maps, start=1):
        assert "OUT1" in prompt, "every map call sees the document overview"
        assert f"part {i} of 3" in prompt
    assert "OUT1" in final and all(f"OUT{i}" in final for i in (2, 3, 4))
    # Notes repeat their headings per part; finalize must merge, not restart.
    assert "NOTES ON PART 3 OF 3" in final
    assert "exactly once" in final
    assert summary == "OUT5"


def test_reduce_runs_only_when_the_notes_overflow(monkeypatch, small_budget):
    prompts: list[str] = []

    def long_notes(llm, prompt):
        prompts.append(prompt)
        return "N" * 4000  # 3 x 4000 chars of notes > the 6000-char budget

    monkeypatch.setattr(agent, "make_llm", lambda *a, **k: object())
    monkeypatch.setattr(agent, "run_prompt", long_notes)
    agent.run(text="A" * 15000, template_id="bullets", model_id="fast")
    # overview + 3 map + 1 reduce + finalize
    assert len(prompts) == 6


def test_empty_text_raises(recorder):
    with pytest.raises(ValueError):
        agent.run(text="   ", template_id="bullets", model_id="fast")


def test_progress_reaches_completion(recorder):
    events: list[tuple[float, str]] = []
    agent.run(
        text="A short document.",
        template_id="bullets",
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
        template_id="bullets",
        model_id="fast",
        on_progress=lambda frac, label: events.append(frac),
    )
    assert events == sorted(events), f"progress bar ran backwards: {events}"
    assert events[-1] == 1.0


def test_pdf_is_converted_to_markdown_before_summarizing(recorder, pdf_bytes, stub_ollama):
    agent.run(filename="report.pdf", data=pdf_bytes, template_id="bullets", model_id="fast")
    assert stub_ollama.rewritten, "the PDF must be converted to Markdown first"
    # The finalize prompt receives the converted Markdown, not the raw text layer.
    assert "# Rewritten" in recorder[-1]


def test_fast_pdf_skips_the_per_page_rewrite(recorder, pdf_bytes, stub_ollama):
    """fast=True uses the digital page's text layer verbatim: no rewrite call."""
    agent.run(
        filename="report.pdf",
        data=pdf_bytes,
        template_id="bullets",
        model_id="fast",
        fast=True,
    )
    assert not stub_ollama.rewritten, "fast mode must not LLM-rewrite digital pages"


def test_explicit_target_language_in_finalize_prompt(recorder):
    agent.run(text="A short document.", template_id="bullets", model_id="fast", target_language="de")
    assert "German" in recorder[-1]


def test_auto_language_detected_for_finalize(recorder):
    agent.run(
        text="This is clearly written in the English language for testing.",
        template_id="bullets",
        model_id="fast",
    )
    assert "English" in recorder[-1]


def test_hybrid_uses_small_model_for_chunks_and_big_for_final(monkeypatch, small_budget):
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

    agent.run(text="A" * 15000, template_id="bullets", model_id="hybrid")
    tags = [tag for tag, _ in used]
    # overview + 3 map on the small model, then one finalize on the big one.
    assert tags == ["gemma4:e4b"] * 4 + ["qwen3.8-27b:latest"]
    assert unloaded == ["gemma4:e4b"]


def test_hybrid_single_chunk_goes_straight_to_big_model(monkeypatch):
    used: list[str] = []
    unloaded: list[str] = []
    monkeypatch.setattr(agent, "make_llm", lambda tag, host=None: tag)
    monkeypatch.setattr(agent, "run_prompt", lambda llm, p: (used.append(llm), "X")[1])
    monkeypatch.setattr(agent, "unload", lambda tag, host=None: unloaded.append(tag))
    agent.run(text="Short.", template_id="bullets", model_id="hybrid")
    assert used == ["qwen3.8-27b:latest"]
    assert unloaded == []
