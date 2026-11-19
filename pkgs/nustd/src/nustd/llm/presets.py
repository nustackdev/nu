"""Providers for LLMFabric. ``endpoint`` is generic; the rest are convenience presets.

One wire (OpenAI-compatible /v1/chat/completions) covers OpenAI, OpenRouter,
Groq, Cerebras, xAI, vLLM, Ollama. Each preset just fills base_url + api_key.

Every preset shares the same tail: ``tags`` for the binding (read it back with
a custom ref), ``body`` for the tree that runs with the endpoint bound, and
``**defaults``, the request-body keys every call inherits (``temperature``,
``max_tokens``, ...). A call kwarg of the same name wins.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from nu.context.fabric import Provide

from .fabric import LLMFabric


if TYPE_CHECKING:
    from collections.abc import Sequence

    from nu.lang import Nu


__all__ = ["cerebras", "endpoint", "groq", "ollama", "openai", "openrouter", "vllm", "xai"]


def endpoint(
    base_url: str,
    *,
    api_key: str = "",
    model: str = "",
    timeout: float = 120.0,
    headers: dict[str, str] | None = None,
    tags: Sequence[object] = (),
    body: Nu | None = None,
    **defaults: object,
) -> Provide:
    """Binds an OpenAI-compatible chat endpoint for the body's duration.

    The generic form the presets all funnel through.

    Args:
        base_url: scheme, host and port, plus any provider path prefix. The
            ``/v1/chat/completions`` path is added by the fabric.
        api_key: sent as an ``Authorization: Bearer`` header unless
            ``headers`` already carries one. Empty sends none.
        model: the fallback model; a default or a call kwarg overrides it.
        timeout: seconds before a request gives up.
        headers: extra request headers.
        tags: tags for the binding, so two endpoints in one scope can be told
            apart. ``LLMRef`` reads the untagged one.
        body: the tree that runs with the endpoint bound. Leave it out to use
            the preset inside a ``With``.
        **defaults: request-body keys every call inherits.

    Notes:
        - The HTTP client opens when the bracket is entered and closes when
          it exits, so calls outside it raise.
        - If no layer sets ``model`` by the time a call runs, it raises.

    Yields:
        A ``Provide`` bracket binding the ``LLMFabric``.

    Example:
        nu.With(nustd.llm.endpoint("http://red:8000", model="qwen3"), body=...)
    """
    kwargs = {
        "base_url": base_url,
        "api_key": api_key,
        "model": model,
        "timeout": timeout,
        "headers": headers,
        "defaults": defaults,
    }
    return Provide(LLMFabric, kwargs, body, tags=tuple(tags))


def ollama(
    *,
    host: str = "localhost",
    port: int = 11434,
    model: str = "",
    timeout: float = 120.0,
    tags: Sequence[object] = (),
    body: Nu | None = None,
    **defaults: object,
) -> Provide:
    """Binds a local or cluster Ollama daemon over its OpenAI-compatible API.

    Args:
        host: machine running the daemon.
        port: the daemon's port.
        model: fallback model tag; may be left empty and set per call.
        timeout: seconds before the request gives up.
        tags: tags for the binding.
        body: the tree that runs with the endpoint bound.
        **defaults: request-body keys every call inherits.

    Notes:
        - No API key: Ollama does not authenticate.
        - The generous default timeout is deliberate. A cold model is loaded
          from disk on first call and that can outlast a normal HTTP timeout.
        - ``model`` is an Ollama tag (``qwen2.5:7b-instruct``), not an
          OpenAI model name.
    """
    return endpoint(
        f"http://{host}:{port}", model=model, timeout=timeout, tags=tags, body=body, **defaults
    )


def openai(
    *,
    api_key: str,
    model: str = "gpt-4o-mini",
    tags: Sequence[object] = (),
    body: Nu | None = None,
    **defaults: object,
) -> Provide:
    """Binds OpenAI's own hosted API.

    Args:
        api_key: an OpenAI key, sent as a bearer token.
        model: fallback model; overridable per call.
        tags: tags for the binding.
        body: the tree that runs with the endpoint bound.
        **defaults: request-body keys every call inherits.
    """
    return endpoint(
        "https://api.openai.com", api_key=api_key, model=model, tags=tags, body=body, **defaults
    )


def openrouter(
    *,
    api_key: str,
    model: str,
    tags: Sequence[object] = (),
    body: Nu | None = None,
    **defaults: object,
) -> Provide:
    """Binds OpenRouter, which fronts many vendors behind one key.

    Args:
        api_key: an OpenRouter key, sent as a bearer token.
        model: required, since there is no sensible default across
            thousands of models. Vendor-qualified, e.g.
            ``anthropic/claude-sonnet-4``.
        tags: tags for the binding.
        body: the tree that runs with the endpoint bound.
        **defaults: request-body keys every call inherits.
    """
    return endpoint(
        "https://openrouter.ai/api", api_key=api_key, model=model, tags=tags, body=body, **defaults
    )


def groq(
    *,
    api_key: str,
    model: str = "llama-3.3-70b-versatile",
    tags: Sequence[object] = (),
    body: Nu | None = None,
    **defaults: object,
) -> Provide:
    """Binds Groq's LPU-hosted open-weight models.

    Args:
        api_key: a Groq key, sent as a bearer token.
        model: fallback model; overridable per call.
        tags: tags for the binding.
        body: the tree that runs with the endpoint bound.
        **defaults: request-body keys every call inherits.

    Notes:
        - Groq's OpenAI-compatible surface lives under an ``/openai`` path
          prefix rather than at the domain root.
    """
    return endpoint(
        "https://api.groq.com/openai",
        api_key=api_key,
        model=model,
        tags=tags,
        body=body,
        **defaults,
    )


def cerebras(
    *,
    api_key: str,
    model: str,
    tags: Sequence[object] = (),
    body: Nu | None = None,
    **defaults: object,
) -> Provide:
    """Binds Cerebras' wafer-scale inference API.

    Args:
        api_key: a Cerebras key, sent as a bearer token.
        model: required; the catalogue is small and moves, so no default
            is guessed.
        tags: tags for the binding.
        body: the tree that runs with the endpoint bound.
        **defaults: request-body keys every call inherits.
    """
    return endpoint(
        "https://api.cerebras.ai", api_key=api_key, model=model, tags=tags, body=body, **defaults
    )


def xai(
    *,
    api_key: str,
    model: str = "grok-2-latest",
    tags: Sequence[object] = (),
    body: Nu | None = None,
    **defaults: object,
) -> Provide:
    """Binds xAI's Grok API.

    Args:
        api_key: an xAI key, sent as a bearer token.
        model: fallback model; overridable per call.
        tags: tags for the binding.
        body: the tree that runs with the endpoint bound.
        **defaults: request-body keys every call inherits.
    """
    return endpoint(
        "https://api.x.ai", api_key=api_key, model=model, tags=tags, body=body, **defaults
    )


def vllm(
    *,
    base_url: str,
    model: str,
    api_key: str = "",
    tags: Sequence[object] = (),
    body: Nu | None = None,
    **defaults: object,
) -> Provide:
    """Binds a vLLM server you run yourself.

    Args:
        base_url: scheme, host and port of the server, e.g.
            ``http://red:8000``. No path: the ``/v1`` prefix is added by
            the fabric.
        model: required, and must match the name the server was launched
            with, since vLLM serves exactly one.
        api_key: only needed when the server was started with one.
        tags: tags for the binding.
        body: the tree that runs with the endpoint bound.
        **defaults: request-body keys every call inherits.
    """
    return endpoint(base_url, api_key=api_key, model=model, tags=tags, body=body, **defaults)
