"""LLM access for the agent layer. LangChain is allowed in this module."""

from __future__ import annotations

from langchain_ollama import ChatOllama

from src.models import num_ctx

# Upper bound on one answer: the 2-page template is ~2000 tokens, map notes on
# a 90k-char part reach ~3400. Guards against a runaway repetition loop.
NUM_PREDICT = 6144
# Thinking models (qwen3.8, qwen3, gemma4) otherwise spend thousands of hidden
# tokens reasoning before answering: ~4x slower, and the budget can run out
# mid-thought, leaving an empty answer. Summarizing needs no chain of thought.
REASONING = False


def make_llm(tag: str, host: str | None = None, temperature: float = 0.2):
    """Build a ChatOllama client for ``tag`` with its measured context window.

    The window is set explicitly per model (``models.NUM_CTX``): left unset,
    Ollama allocates the trained maximum, which spills large models off the GPU.
    """
    kwargs = {
        "model": tag,
        "temperature": temperature,
        "num_ctx": num_ctx(tag),
        "num_predict": NUM_PREDICT,
        "reasoning": REASONING,
    }
    if host:
        kwargs["base_url"] = host
    return ChatOllama(**kwargs)


def run_prompt(llm, prompt: str) -> str:
    """Invoke ``llm`` with a text prompt and return stripped text content."""
    return llm.invoke(prompt).content.strip()
