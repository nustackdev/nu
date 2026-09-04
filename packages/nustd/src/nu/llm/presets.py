"""Providers for LLMFabric. `bind` is generic; the rest are convenience presets.

One wire (OpenAI-compatible /v1/chat/completions) covers OpenAI, OpenRouter,
Groq, Cerebras, xAI, vLLM, Ollama. Each preset just fills base_url + api_key.
"""

from __future__ import annotations

from nu.context.fabric import Provide

from .fabric import LLMFabric


__all__ = ["bind", "cerebras", "groq", "ollama", "openai", "openrouter", "vllm", "xai"]


def bind(service_cls: type, **defaults: object) -> Provide:
    """Point every ChatRef on a Service at one endpoint, for the scope it is provided in.

    The generic form the presets all funnel through. What it provides is
    tagged by the Service class, which is how a ChatRef declared on that
    class finds its fabric and how two Services can sit on two providers in
    the same program.

    Args:
        service_cls: the Service whose ChatRefs this endpoint serves.
        **defaults: constructor kwargs for the fabric - ``base_url``
            (required), ``api_key``, ``model``, ``timeout``, ``headers``.

    Notes:
        - The kwargs it accepts are ``base_url`` (required), ``api_key``,
          ``model``, ``timeout`` and ``headers``. The presets are exactly
          this call with the first two filled in.
        - The HTTP client opens when the ``With`` block is entered and
          closes when it exits, so calls outside the block raise.
        - ``api_key`` becomes an ``Authorization: Bearer`` header unless
          ``headers`` already carries one.
        - ``model`` here is the fallback; a declaration default or a call
          kwarg overrides it.

    Yields:
        A Provide to hand to ``nu.With``.

    Example:
        app = nu.With(nu.llm.bind(Bot, base_url="http://red:8000", model="qwen3"), body=...)
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
    """Bind a Service to a local or cluster Ollama daemon over its OpenAI-compatible API.

    Args:
        service_cls: the Service whose ChatRefs this endpoint serves.
        host: machine running the daemon.
        port: the daemon's port.
        model: fallback model tag; may be left empty and set per call.
        timeout: seconds before the request gives up.

    Notes:
        - No API key: Ollama does not authenticate, so no Authorization
          header is sent.
        - The generous default timeout is deliberate. A cold model is
          loaded from disk on first call and that can outlast a normal HTTP
          timeout.
        - ``model`` is an Ollama tag (``qwen2.5:7b-instruct``), not an
          OpenAI model name.
    """
    return bind(
        service_cls,
        base_url=f"http://{host}:{port}",
        model=model,
        timeout=timeout,
    )


def openai(service_cls: type, *, api_key: str, model: str = "gpt-4o-mini") -> Provide:
    """Bind a Service to OpenAI's own hosted API.

    Args:
        service_cls: the Service whose ChatRefs this endpoint serves.
        api_key: an OpenAI key, sent as a bearer token.
        model: fallback model; overridable per declaration or per call.
    """
    return bind(
        service_cls,
        base_url="https://api.openai.com",
        api_key=api_key,
        model=model,
    )


def openrouter(service_cls: type, *, api_key: str, model: str) -> Provide:
    """Bind a Service to OpenRouter, which fronts many vendors behind one key.

    Args:
        service_cls: the Service whose ChatRefs this endpoint serves.
        api_key: an OpenRouter key, sent as a bearer token.
        model: required, since there is no sensible default across
            thousands of models. Vendor-qualified, e.g.
            ``anthropic/claude-sonnet-4``.
    """
    return bind(
        service_cls,
        base_url="https://openrouter.ai/api",
        api_key=api_key,
        model=model,
    )


def groq(service_cls: type, *, api_key: str, model: str = "llama-3.3-70b-versatile") -> Provide:
    """Bind a Service to Groq's LPU-hosted open-weight models.

    Args:
        service_cls: the Service whose ChatRefs this endpoint serves.
        api_key: a Groq key, sent as a bearer token.
        model: fallback model; overridable per declaration or per call.

    Notes:
        - Groq's OpenAI-compatible surface lives under an ``/openai`` path
          prefix rather than at the domain root.
    """
    return bind(
        service_cls,
        base_url="https://api.groq.com/openai",
        api_key=api_key,
        model=model,
    )


def cerebras(service_cls: type, *, api_key: str, model: str) -> Provide:
    """Bind a Service to Cerebras' wafer-scale inference API.

    Args:
        service_cls: the Service whose ChatRefs this endpoint serves.
        api_key: a Cerebras key, sent as a bearer token.
        model: required; the catalogue is small and moves, so no default
            is guessed.
    """
    return bind(
        service_cls,
        base_url="https://api.cerebras.ai",
        api_key=api_key,
        model=model,
    )


def xai(service_cls: type, *, api_key: str, model: str = "grok-2-latest") -> Provide:
    """Bind a Service to xAI's Grok API.

    Args:
        service_cls: the Service whose ChatRefs this endpoint serves.
        api_key: an xAI key, sent as a bearer token.
        model: fallback model; overridable per declaration or per call.
    """
    return bind(
        service_cls,
        base_url="https://api.x.ai",
        api_key=api_key,
        model=model,
    )


def vllm(service_cls: type, *, base_url: str, model: str, api_key: str = "") -> Provide:
    """Bind a Service to a vLLM server you run yourself.

    Args:
        service_cls: the Service whose ChatRefs this endpoint serves.
        base_url: scheme, host and port of the server, e.g.
            ``http://red:8000``. No path: the ``/v1`` prefix is added by
            the fabric.
        model: required, and must match the name the server was launched
            with, since vLLM serves exactly one.
        api_key: only needed when the server was started with one.
    """
    return bind(service_cls, base_url=base_url, api_key=api_key, model=model)
