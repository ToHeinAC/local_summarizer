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
