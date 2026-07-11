"""LLM access for the agent layer. LangChain is allowed in this module."""

from __future__ import annotations

from langchain_ollama import ChatOllama

# Cap the KV-cache context. Without this Ollama allocates the model's full
# trained window (128k for gemma4), which balloons VRAM and cuts throughput
# ~5x. Every workload here (6000-char chunks, reduce batches, finalize) fits
# well under 8192 tokens, so the cap costs no precision.
NUM_CTX = 8192


def make_llm(tag: str, host: str | None = None, temperature: float = 0.2):
    """Build a ChatOllama client for the given Ollama model ``tag``."""
    kwargs = {"model": tag, "temperature": temperature, "num_ctx": NUM_CTX}
    if host:
        kwargs["base_url"] = host
    return ChatOllama(**kwargs)


def run_prompt(llm, prompt: str) -> str:
    """Invoke ``llm`` with a text prompt and return stripped text content."""
    return llm.invoke(prompt).content.strip()
