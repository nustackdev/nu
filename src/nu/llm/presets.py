"""Providers for LLMFabric. `bind` is generic; the rest are convenience presets.

One wire (OpenAI-compatible /v1/chat/completions) covers OpenAI, OpenRouter,
Groq, Cerebras, xAI, vLLM, Ollama. Each preset just fills base_url + api_key.
"""

from __future__ import annotations

from nu.context.fabric import Provide

from .fabric import LLMFabric


__all__ = ["bind", "cerebras", "groq", "ollama", "openai", "openrouter", "vllm", "xai"]


def bind(service_cls: type, **defaults: object) -> Provide:
    """Provide an LLMFabric tagged by the service class.

    Kwargs: `base_url`, `api_key`, `model`, `timeout`, `headers`.
    """
    return Provide(LLMFabric, defaults, tag=service_cls)


def ollama(
    service_cls: type,
    *,
    host: str = "localhost",
    port: int = 11434,
    model: str = "",
    timeout: float = 120.0,
) -> Provide:
    """Ollama on `http://{host}:{port}/v1`. Set `model=` here or per call."""
    return bind(
        service_cls,
        base_url=f"http://{host}:{port}",
        model=model,
        timeout=timeout,
    )


def openai(service_cls: type, *, api_key: str, model: str = "gpt-4o-mini") -> Provide:
    """OpenAI api.openai.com."""
    return bind(
        service_cls,
        base_url="https://api.openai.com",
        api_key=api_key,
        model=model,
    )


def openrouter(service_cls: type, *, api_key: str, model: str) -> Provide:
    """OpenRouter openrouter.ai — thousands of models, one key."""
    return bind(
        service_cls,
        base_url="https://openrouter.ai/api",
        api_key=api_key,
        model=model,
    )


def groq(service_cls: type, *, api_key: str, model: str = "llama-3.3-70b-versatile") -> Provide:
    """Groq api.groq.com — fast inference."""
    return bind(
        service_cls,
        base_url="https://api.groq.com/openai",
        api_key=api_key,
        model=model,
    )


def cerebras(service_cls: type, *, api_key: str, model: str) -> Provide:
    """Cerebras api.cerebras.ai."""
    return bind(
        service_cls,
        base_url="https://api.cerebras.ai",
        api_key=api_key,
        model=model,
    )


def xai(service_cls: type, *, api_key: str, model: str = "grok-2-latest") -> Provide:
    """XAI api.x.ai (Grok)."""
    return bind(
        service_cls,
        base_url="https://api.x.ai",
        api_key=api_key,
        model=model,
    )


def vllm(service_cls: type, *, base_url: str, model: str, api_key: str = "") -> Provide:
    """VLLM self-hosted at `base_url` (e.g. `http://red:8000`)."""
    return bind(service_cls, base_url=base_url, api_key=api_key, model=model)
