"""Test carriers for Dyn: scalar-yielding atoms that return Nu terms.

Each carrier is a ScalarQuery whose evaluation returns a Nu term (the inner
Dyn payload). Kept in ``_support/`` because both attribute tests and runtime
tests reach for the same shapes.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from nu.engine.structure import Declared
from nu.lang import ScalarQuery


if TYPE_CHECKING:
    from collections.abc import Callable

    from nu.lang import Nu
    from nu.lang.runtime import Runtime


__all__ = [
    "AsyncOnlyCarrier",
    "ConstCarrier",
    "SyncOnlyCarrier",
]


class ConstCarrier(ScalarQuery):
    """A scalar-yielding carrier that returns a fixed Nu term when evaluated."""

    def __init__(self, term: Nu) -> None:
        super().__init__()
        self._payload["inner"] = term

    def _compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        inner = self._payload["inner"]

        def thunk(rt: Runtime) -> object:
            return inner

        return thunk

    def _acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        inner = self._payload["inner"]

        async def athunk(rt: Runtime) -> object:
            return inner

        return athunk


class AsyncOnlyCarrier(ScalarQuery):
    """A carrier declared async-only (folds into HAS_ASYNC_ONLY_ATOM)."""

    _requires_async = Declared(value=True, name="requires_async")

    def __init__(self, term: Nu) -> None:
        super().__init__()
        self._payload["inner"] = term

    def _compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        inner = self._payload["inner"]

        def thunk(rt: Runtime) -> object:
            return inner

        return thunk

    def _acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        inner = self._payload["inner"]

        async def athunk(rt: Runtime) -> object:
            return inner

        return athunk


class SyncOnlyCarrier(ScalarQuery):
    """A carrier declared sync-only (folds into HAS_SYNC_ONLY_ATOM)."""

    async_affinity = Declared(value=False)

    def __init__(self, term: Nu) -> None:
        super().__init__()
        self._payload["inner"] = term

    def _compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        inner = self._payload["inner"]

        def thunk(rt: Runtime) -> object:
            return inner

        return thunk

    def _acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        inner = self._payload["inner"]

        async def athunk(rt: Runtime) -> object:
            return inner

        return athunk
