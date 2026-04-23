"""Typed reference to storage location.

Nu                          - the primitive
├── LValue                  - addressable location
│   └── Ref                 - typed pointer to storage location

Core vocabulary:
    resolve(ctx) -> Location    - WHERE is this? (identity/path)
    fetch(ctx) -> T | Sentinel  - WHAT is there? (value extraction)
    open(ctx)                   - Nu evaluator primitive; yields fetched value once
"""

from __future__ import annotations

import inspect
from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Any

from .nu import LValue
from .types import Mode, Sentinel, T_co


if TYPE_CHECKING:
    from collections.abc import AsyncGenerator, Generator

    from ..context import Context


__all__ = [
    "Ref",
]


_VALID_MODE_PAIRS: frozenset[tuple[Mode, Mode]] = frozenset(
    {
        (Mode.SYNC, Mode.SYNC),
        (Mode.BOTH, Mode.SYNC),
        (Mode.BOTH, Mode.BOTH),
        (Mode.ASYNC, Mode.ASYNC),
    }
)


class Ref(LValue[T_co | Sentinel], ABC):
    """Typed pointer to a location. Pure protocol.

    - `aresolve()` / `resolve()` build identity/location.
    - `afetch()` / `fetch()` extract the value.
    - `aopen()` / `open()` are Nu evaluator primitives; yield the fetched value once.

    Mode enforcement mirrors Interaction: every concrete subclass declares
    `own_mode` and `func_mode` in its own __dict__; the pair must be one of
    (SYNC,SYNC), (BOTH,SYNC), (BOTH,BOTH), (ASYNC,ASYNC).
    """

    def __init_subclass__(cls, **kwargs: Any) -> None:
        super().__init_subclass__(**kwargs)
        if ABC in cls.__bases__ or inspect.isabstract(cls):
            return
        for name in ("own_mode", "func_mode"):
            if name not in cls.__dict__:
                msg = (
                    f"{cls.__module__}.{cls.__qualname__} must declare "
                    f"`{name}` explicitly (Mode.SYNC, Mode.ASYNC, or Mode.BOTH). "
                    "Inheritance is not enough — explicit is better than implicit."
                )
                raise TypeError(msg)
        pair = (cls.own_mode, cls.func_mode)
        if pair not in _VALID_MODE_PAIRS:
            msg = (
                f"{cls.__module__}.{cls.__qualname__} declares "
                f"own_mode={cls.own_mode.name}, func_mode={cls.func_mode.name}. "
                "Valid pairs: (SYNC,SYNC), (BOTH,SYNC), (BOTH,BOTH), "
                "(ASYNC,ASYNC). See projects/nu/model/programming/modes.md."
            )
            raise TypeError(msg)

    @abstractmethod
    async def aresolve(self, ctx: Context) -> object:
        """Build identity/location for this reference."""
        ...

    @abstractmethod
    async def afetch(self, ctx: Context) -> T_co | Sentinel:
        """Extract value from this location."""
        ...

    def resolve(self, ctx: Context) -> object:
        """Sync counterpart of resolve. Override for BOTH Refs."""
        msg = f"{type(self).__name__} has no sync resolve; ASYNC-only Ref"
        raise RuntimeError(msg)

    def fetch(self, ctx: Context) -> T_co | Sentinel:
        """Sync counterpart of fetch. Override for BOTH Refs."""
        msg = f"{type(self).__name__} has no sync fetch; ASYNC-only Ref"
        raise RuntimeError(msg)

    async def aopen(self, ctx: Context) -> AsyncGenerator[T_co | Sentinel, None]:
        """Yield the fetched value once."""
        yield await self.afetch(ctx)

    def open(self, ctx: Context) -> Generator[T_co | Sentinel, None, None]:
        """Yield the fetched value once (sync).

        Gated by effective_mode (subtree sup), not own_mode: a BOTH ref with
        an ASYNC address child cannot run sync.
        """
        if self.effective_mode is Mode.ASYNC:
            msg = (
                f"{type(self).__name__} has ASYNC in its subtree; "
                "cannot run sync."
            )
            raise RuntimeError(msg)
        yield self.fetch(ctx)

    @property
    def is_self_pure(self) -> bool:
        """Refs are always pure. Reading doesn't mutate state."""
        return True
