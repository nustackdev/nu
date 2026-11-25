"""``LLMRef``: the fabric ref that resolves the ``LLMFabric`` bound on ctx.

A plain ``FabricRef``: the address is the fabric type, so the read is the
untagged binding, same as ``nustd.valkey.ValkeyRef``. It also carries this
fabric's fluent surface: ``LLMRef().chat(prompt=...)`` and
``Chat(LLMRef(), prompt=...)`` build the same term, and ``chat_stream`` does
the same for ``ChatStream``.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from nu.context import FabricRef
from nu.forms import Iterator

from .fabric import LLMFabric


if TYPE_CHECKING:
    from .interactions import Chat


__all__ = ["LLMRef"]


class LLMRef(FabricRef):
    """The ``LLMFabric`` bound on the Context.

    Notes:
        - Reading it is a lookup and nothing else; no request is sent.
        - The methods are a convenience over the constructors, each returning
          the same term the matching ``Chat(...)`` / ``ChatStream(...)`` call
          would.

    Yields:
        The bound ``LLMFabric``. NULL when nothing is bound.

    Example:
        llm = nustd.llm.LLMRef()
        app = nustd.llm.ollama(
            host="red",
            model="qwen2.5:7b-instruct",
            body=nu.print(nu.dict(llm.chat(prompt="haiku about rust"))["text"]),
        )
        nu.run(app)
    """

    fabric = LLMFabric

    # The interactions import this module, so the imports below are lazy.

    def chat(self, **kwargs: object) -> Chat:
        """A ``Chat`` on this endpoint: one chat/completions call, yield the reply."""
        from .interactions import Chat

        return Chat(self, **kwargs)

    def chat_stream(self, **kwargs: object) -> Iterator:
        """A ``ChatStream`` on this endpoint: the reply's text deltas as they arrive."""
        from .interactions import ChatStream

        return Iterator(ChatStream(self, **kwargs))
