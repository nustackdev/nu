"""MethodRef: leaf Ref addressing a Method on a Service."""

from __future__ import annotations

from typing import TYPE_CHECKING, cast

from nu.lang import Literal, Ref


if TYPE_CHECKING:
    from collections.abc import Callable

    from nu.lang.runtime import Runtime

    from .dsl import Method

__all__ = ["MethodRef"]


class MethodRef(Ref):
    """A Ref addressing a Method on a Service.

    The address (``name``, ``owner_service``) is its fields. Any extra config
    the declaration carries (a path, a verb, call defaults) is its one child,
    a ``Literal`` dict, so the ref evaluates to ``{name, owner_service,
    **config}``.
    """

    def __init__(
        self,
        *,
        name: str,
        owner_service: type | None = None,
        **config: object,
    ) -> None:
        super().__init__(Literal(dict(config)))
        self._name: str = name
        self._owner_service: type | None = owner_service

    @classmethod
    def method(cls, **kwargs: object) -> Method:
        """Package this MethodRef class + config as a Method declaration."""
        from .dsl import Method

        return Method(cls, **kwargs)

    def _snapshot(self, config: object) -> dict[str, object]:
        """The name, the owning service and the extra config, as one dict."""
        return {"name": self._name, "owner_service": self._owner_service, **cast("dict", config)}

    def _compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        """Evaluate to a snapshot of the address and its extra config."""
        config_thunk = children[0]

        def thunk(rt: Runtime) -> dict:
            return self._snapshot(config_thunk(rt))

        return thunk

    def _acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        """Async sibling of _compile."""
        config_thunk = children[0]

        async def athunk(rt: Runtime) -> dict:
            return self._snapshot(await config_thunk(rt))

        return athunk
