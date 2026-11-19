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
    """A Ref addressing a Method on a Service.

    Childless. The address (``name``, ``owner_service``) and any extra
    config the declaration carries (a path, a verb, call defaults) are its
    fields: the service class sets them once, they describe the method
    rather than a value the tree computes. The ref evaluates to a fresh
    ``{name, owner_service, **config}`` each time.
    """

    def __init__(
        self,
        *,
        name: str,
        owner_service: type | None = None,
        **config: object,
    ) -> None:
        super().__init__()
        self._name: str = name
        self._owner_service: type | None = owner_service
        self._config: dict[str, object] = dict(config)

    @classmethod
    def method(cls, **kwargs: object) -> Method:
        """Package this MethodRef class + config as a Method declaration."""
        from .dsl import Method

        return Method(cls, **kwargs)

    def _snapshot(self) -> dict[str, object]:
        """The name, the owning service and the extra config, as one fresh dict."""
        return {"name": self._name, "owner_service": self._owner_service, **self._config}

    def _compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        """Evaluate to a snapshot of the address and its extra config."""
        snapshot = self._snapshot

        def thunk(rt: Runtime) -> dict:
            return snapshot()

        return thunk

    def _acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        """Async sibling of _compile."""
        snapshot = self._snapshot

        async def athunk(rt: Runtime) -> dict:
            return snapshot()

        return athunk
