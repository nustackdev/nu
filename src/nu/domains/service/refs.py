"""MethodRef: leaf Ref addressing a Method on a Service."""

from __future__ import annotations

from typing import TYPE_CHECKING

from nu.lang import Ref


if TYPE_CHECKING:
    from collections.abc import Callable

    from nu.lang.runtime import Runtime

    from .dsl import Method

__all__ = ["MethodRef"]


class MethodRef(Ref):
    """A Ref addressing a Method on a Service. Leaf: address rides in _payload."""

    def __init__(
        self,
        *,
        name: str,
        owner_service: type | None = None,
        **payload: object,
    ) -> None:
        super().__init__()
        self._payload["name"] = name
        self._payload["owner_service"] = owner_service
        for k, v in payload.items():
            self._payload[k] = v

    @classmethod
    def method(cls, **kwargs: object) -> Method:
        """Package this MethodRef class + config as a Method declaration."""
        from .dsl import Method

        return Method(cls, **kwargs)

    def _compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        """Evaluate to a snapshot of _payload."""
        snapshot = dict(self._payload)

        def thunk(rt: Runtime) -> dict:
            return snapshot

        return thunk

    def _acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        """Async sibling of _compile."""
        snapshot = dict(self._payload)

        async def athunk(rt: Runtime) -> dict:
            return snapshot

        return athunk
