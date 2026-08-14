"""ChatRef: Ref addressing a chat/completions endpoint on a Service.

Call it with `prompt="..."` (sugar for a single user message) or
`messages=[{"role":..., "content":...}, ...]`. Extra kwargs (model,
temperature, max_tokens, stop, ...) pass straight into the request body.
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
    """Chat completions endpoint Ref."""

    @classmethod
    def method(cls, **defaults: object) -> ChatRef:  # type: ignore[override]
        """Declare a chat endpoint. Defaults merge with per-call overrides."""
        return Method(cls, defaults=defaults)  # type: ignore[return-value]

    def __call__(self, **kwargs: object) -> Nu:
        """Run one chat turn. Pass `prompt=...` or `messages=[...]`; extras override."""
        return Chat(self, Dict.of(**kwargs))
