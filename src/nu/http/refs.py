"""HttpMethodRef: MethodRef subclass whose call constructs an HTTP interaction."""

from __future__ import annotations

from typing import TYPE_CHECKING

from nu.domains.service import MethodRef


if TYPE_CHECKING:
    from nu.lang import Nu

__all__ = ["HttpMethodRef"]


class HttpMethodRef(MethodRef):
    """Calling with kwargs constructs the interaction matching the declared verb."""

    def __call__(self, **kwargs: object) -> Nu:
        """`SolanaRPC.get_balance(pubkey=...)` -> HttpGet(self, kwargs)."""
        from .interactions import verb_to_cls

        verb = self._payload["verb"]
        cls = verb_to_cls(verb)
        return cls(self, kwargs)
