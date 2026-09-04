"""ChatRef: Ref addressing a chat/completions endpoint on a Service.

Mirrors the nu.http verb refs: `.method(**defaults)` returns a Method
declaration that the ServiceMeta descriptor unwraps at class access, and
calling the Ref with kwargs produces a Chat interaction.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from nu.domains.service import Method, MethodRef
from nu.forms import Dict

from .interactions import Chat


if TYPE_CHECKING:
    from nu.lang import Nu


__all__ = ["ChatRef"]


class ChatRef(MethodRef):
    """Addresses an OpenAI-compatible chat/completions endpoint on a Service.

    Written in a Service class body, one Ref per endpoint the Service talks
    to. The Ref names no host, key or model of its own: which endpoint it
    reaches is decided at run time by whichever ``LLMFabric`` was provided
    for the owning Service class, so the same declaration can be pointed at
    Ollama, OpenRouter or a self-hosted vLLM without being rewritten.

    Notes:
        - Resolution is by owning Service class, so two Services in one
          program can hold ChatRefs against different providers.
        - The endpoint path is fixed at ``/v1/chat/completions``; only the
          base URL varies per provider.
        - Nothing here is checked against a provider's schema. Unknown keys
          travel into the request body and the provider decides.

    Example:
        class Bot(nu.Service):
            chat = nu.llm.ChatRef.method(temperature=0.7)
        app = nu.With(
            nu.llm.ollama(Bot, host="red", model="qwen2.5:7b-instruct"),
            body=nu.print(nu.dict(Bot.chat(prompt="haiku about rust"))["text"]),
        )
        nu.run(app)
    """

    @classmethod
    def method(cls, **defaults: object) -> ChatRef:  # type: ignore[override]
        """Declare a chat endpoint whose defaults every call through it inherits.

        Args:
            **defaults: request-body keys the endpoint always sends
                (``model``, ``temperature``, ``max_tokens``, ``stop``, ...).
                A per-call kwarg of the same name wins.

        Notes:
            - Annotated as returning the Ref, but at run time it returns a
              ``Method`` declaration that the ServiceMeta descriptor unwraps
              at class access. The lie makes ``Bot.chat`` type-check as a
              ChatRef.
            - Three layers can set ``model``: the bind, these defaults, and
              the call, innermost winning. If it is still empty when the
              call runs, the fabric raises.
        """
        return Method(cls, defaults=defaults)  # type: ignore[return-value]

    def __call__(self, **kwargs: object) -> Nu:
        """Build a Chat interaction over one turn's request body.

        Args:
            **kwargs: either ``prompt=`` (sugar for one user message) or
                ``messages=`` (a full role/content list), plus any request
                body keys to override the endpoint defaults for this call.

        Notes:
            - Takes only keywords: ``prompt=`` (sugar for one user message)
              or ``messages=`` (a role/content list), plus any request-body
              keys overriding the endpoint defaults for this call.
            - Exactly one of ``prompt`` or ``messages`` is needed; with
              neither, the call raises when it runs, not when it is built.
            - ``messages`` wins when both are given, and ``prompt`` is
              dropped.
            - Every kwarg is captured into a ``Dict`` child, so the values
              may themselves be Nu terms resolved at evaluation.
        """
        return Chat(self, Dict.of(**kwargs))
