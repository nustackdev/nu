"""The interactions of the ``nustd.llm`` fabric.

Two reads over one ``LLMFabric``: the whole reply, or the reply as it streams.

==========  ==============  ===========
atom        slots           sort
==========  ==============  ===========
Chat        (llm, args)     ScalarQuery
ChatStream  (llm, args)     StreamQuery
==========  ==============  ===========

Both take the same kwargs: either ``prompt=`` (sugar for one user message) or
``messages=`` (a role/content list), plus any request-body keys (``model``,
``temperature``, ``max_tokens``, ...) for this call. Every kwarg is captured
into a ``Dict`` child, so the values may themselves be Nu terms.
"""

from __future__ import annotations

import json
from typing import TYPE_CHECKING, Any

from nu.forms import Dict
from nu.lang import ScalarQuery, StreamQuery
from nu.lang.null import is_null

from .fabric import LLMFabric


if TYPE_CHECKING:
    from collections.abc import AsyncIterator, Callable, Iterator

    from nu.lang import Nu
    from nu.lang.runtime import Runtime


__all__ = ["Chat", "ChatStream"]


def _require_fabric(value: object) -> LLMFabric:
    """Unwrap the endpoint slot's value, refusing NULL with a usable message."""
    if is_null(value) or value is None:
        msg = "no LLMFabric is bound on the Context; wrap the tree in a nustd.llm preset"
        raise RuntimeError(msg)
    if not isinstance(value, LLMFabric):
        msg = f"the llm slot yielded {type(value).__name__}, not an LLMFabric"
        raise TypeError(msg)
    return value


def _split(args: dict) -> tuple[list[dict], dict]:
    """Pull messages out of the call args (or synthesize them from `prompt`)."""
    call = dict(args)
    prompt = call.pop("prompt", None)
    messages = call.pop("messages", None)
    if messages is None:
        if prompt is None:
            msg = "LLM call needs `prompt=...` or `messages=[...]`"
            raise ValueError(msg)
        messages = [{"role": "user", "content": str(prompt)}]
    return list(messages), call


_PATH = "/v1/chat/completions"


def _body(fabric: LLMFabric, args: dict, *, stream: bool = False) -> dict[str, Any]:
    """The request body: fabric defaults under the call's keys, None values dropped."""
    messages, call = _split(args)
    merged = {**fabric.defaults, **call}
    model = merged.pop("model", None) or fabric.model
    if not model:
        msg = "LLMFabric: no model set (pass `model=` on the preset or on the call)"
        raise ValueError(msg)
    body: dict[str, Any] = {"model": model, "messages": messages}
    body.update({k: v for k, v in merged.items() if v is not None})
    if stream:
        body["stream"] = True
    return body


def _reply(data: dict) -> dict[str, Any]:
    """The reply dict ``Chat`` yields, read off one chat/completions response."""
    choice = (data.get("choices") or [{}])[0]
    message = choice.get("message") or {}
    return {
        "text": message.get("content") or "",
        "message": message,
        "model": data.get("model"),
        "usage": data.get("usage"),
        "finish_reason": choice.get("finish_reason"),
    }


def _delta(line: str) -> str | None:
    """The text delta one SSE line carries; None for keep-alives, the end marker, empty deltas."""
    if not line.startswith("data:"):
        return None
    data = line[5:].strip()
    if not data or data == "[DONE]":
        return None
    choice = (json.loads(data).get("choices") or [{}])[0]
    return (choice.get("delta") or {}).get("content") or None


def _stream(fabric: LLMFabric, body: dict) -> Iterator[str]:
    """Sync stream: the reply's text deltas, the request open until exhausted."""
    with fabric.client.stream("POST", _PATH, json=body) as r:
        r.raise_for_status()
        for line in r.iter_lines():
            if (text := _delta(line)) is not None:
                yield text


async def _astream(fabric: LLMFabric, body: dict) -> AsyncIterator[str]:
    """Async stream: the reply's text deltas, the request open until exhausted."""
    async with fabric.aclient.stream("POST", _PATH, json=body) as r:
        r.raise_for_status()
        async for line in r.aiter_lines():
            if (text := _delta(line)) is not None:
                yield text


class Chat(ScalarQuery):
    """One chat/completions request against the bound ``LLMFabric``, the whole reply at once.

    At evaluation it resolves the endpoint, merges the fabric's request
    defaults under this call's kwargs, turns ``prompt`` into a one-message
    list when ``messages`` was not given, and sends the body.

    Args:
        llm: the node yielding the ``LLMFabric``, typically an ``LLMRef``.
        **kwargs: ``prompt=`` or ``messages=``, plus request-body keys.

    Notes:
        - Exactly one of ``prompt`` or ``messages`` is needed; with neither,
          the call raises when it runs. ``messages`` wins when both are given.
        - Keys whose value is None are dropped before the request.
        - No retry, no backoff. A non-2xx response raises through httpx.
        - The sync path holds the thread for the whole round trip. Prefer
          ``nu.arun``.

    Yields:
        A dict with ``text`` (the assistant's content, ``""`` when the
        provider returned none), ``message`` (the raw message object),
        ``model``, ``usage`` and ``finish_reason``. The last three are None
        when the provider omits them.

    Example:
        app = nustd.llm.openai(
            api_key=key,
            body=nu.print(nu.dict(nustd.llm.LLMRef().chat(prompt="yes or no"))["text"]),
        )
        asyncio.run(nu.arun(app))
    """

    def __init__(self, llm: Nu, **kwargs: object) -> None:
        super().__init__(llm, Dict.of(**kwargs))

    def _compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        """Build the sync chat thunk: the fabric's blocking client."""
        llm, args = children

        def thunk(rt: Runtime) -> object:
            fabric = _require_fabric(llm(rt))
            r = fabric.client.post(_PATH, json=_body(fabric, args(rt)))
            r.raise_for_status()
            return _reply(r.json())

        return thunk

    def _acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        """Build the async chat thunk: the fabric's async client."""
        llm, args = children

        async def athunk(rt: Runtime) -> object:
            fabric = _require_fabric(await llm(rt))
            r = await fabric.aclient.post(_PATH, json=_body(fabric, await args(rt)))
            r.raise_for_status()
            return _reply(r.json())

        return athunk


class ChatStream(StreamQuery):
    """One streamed chat/completions request: the reply's text, chunk by chunk.

    Same request as ``Chat``, sent with ``stream: true``. Each item is one
    text delta as the provider sends it; joined, they are the reply's
    ``text``.

    Args:
        llm: the node yielding the ``LLMFabric``, typically an ``LLMRef``.
        **kwargs: ``prompt=`` or ``messages=``, plus request-body keys.

    Notes:
        - Empty deltas (role-only frames, keep-alives) are skipped.
        - Usage and finish reason are not surfaced; use ``Chat`` when you
          need them.
        - The request stays open while the stream is consumed, and closes
          when it is exhausted or abandoned.

    Yields:
        The reply's text deltas, as str.

    Example:
        llm = nustd.llm.LLMRef()
        app = nustd.llm.ollama(
            model="qwen2.5:7b", body=nu.Collect(llm.chat_stream(prompt="haiku"))
        )
        asyncio.run(nu.arun(app))
    """

    def __init__(self, llm: Nu, **kwargs: object) -> None:
        super().__init__(llm, Dict.of(**kwargs))

    def _compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        """Build the sync stream thunk: an iterator over the text deltas."""
        llm, args = children

        def thunk(rt: Runtime) -> object:
            fabric = _require_fabric(llm(rt))
            return _stream(fabric, _body(fabric, args(rt), stream=True))

        return thunk

    def _acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        """Build the async stream thunk: an async iterator over the text deltas."""
        llm, args = children

        async def athunk(rt: Runtime) -> object:
            fabric = _require_fabric(await llm(rt))
            return _astream(fabric, _body(fabric, await args(rt), stream=True))

        return athunk
