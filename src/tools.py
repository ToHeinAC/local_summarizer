"""LLM access for the agent layer. LangChain is allowed in this module."""

from __future__ import annotations

from langchain_ollama import ChatOllama


def make_llm(tag: str, host: str | None = None, temperature: float = 0.2):
    """Build a ChatOllama client for the given Ollama model ``tag``."""
    kwargs = {"model": tag, "temperature": temperature}
    if host:
        kwargs["base_url"] = host
    return ChatOllama(**kwargs)


def run_prompt(llm, prompt: str) -> str:
    """Invoke ``llm`` with a text prompt and return stripped text content."""
    return llm.invoke(prompt).content.strip()
