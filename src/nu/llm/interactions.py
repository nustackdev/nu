"""Chat: ScalarAction that runs one chat/completions call."""

from __future__ import annotations

from typing import TYPE_CHECKING

from nu.engine.structure import Declared
from nu.lang import ScalarAction

from .core import acompile_call, compile_call


if TYPE_CHECKING:
    from collections.abc import Callable


__all__ = ["Chat"]


class Chat(ScalarAction):
    """One chat/completions request against the endpoint a ChatRef addresses.

    Built by calling a ChatRef rather than written by hand. At evaluation it
    resolves the Ref, merges the endpoint's declared defaults under this
    call's kwargs, turns ``prompt`` into a one-message list when ``messages``
    was not given, and hands the body to the ``LLMFabric`` provided for the
    owning Service.

    Args:
        ref: the ChatRef naming the endpoint.
        args: a Dict of this call's request body keys.

    Notes:
        - Declared as mutating its Ref child, so it is never reordered
          against or folded with other calls on the same endpoint.
        - Only the merged body is sent; keys whose value is None are
          dropped before the request.
        - No retry, no backoff, no streaming. A non-2xx response raises
          through httpx rather than yielding a sentinel.
        - The sync path uses the fabric's blocking client, so it holds the
          thread for the whole round trip. Prefer ``nu.arun``.

    Yields:
        A dict with ``text`` (the assistant's content, ``""`` when the
        provider returned none), ``message`` (the raw message object),
        ``model``, ``usage`` and ``finish_reason``. The last three are None
        when the provider omits them.

    Example:
        class Bot(nu.Service):
            chat = nu.llm.ChatRef.method()
        app = nu.With(
            nu.llm.openai(Bot, api_key=key),
            body=nu.print(nu.dict(Bot.chat(prompt="one word: yes or no"))["text"]),
        )
        asyncio.run(nu.arun(app))
    """

    _mutates = Declared(value=frozenset({0}), name="mutates")

    def _compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        return compile_call(children)

    def _acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        return acompile_call(children)
