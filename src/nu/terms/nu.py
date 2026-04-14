"""Nu - the primitive.

Nu is the recursive unit of computation. A Nu is made of Nus.
Both a leaf (Literal(5)) and a full app are Nus.

Hierarchy:
    Nu[T_co]                - base: execute(context) -> T_co
    ├── LValue[T_co]        - addressable location (internal)
    │   └── Ref[T_co]       - typed pointer (see ref.py)
    └── RValue[T_co]        - evaluable expression (internal)
        ├── Literal[T_co]   - literal data (see literal.py)
        └── Op[T_co]        - operation (see op.py)
"""

from __future__ import annotations

from abc import ABC
from contextlib import asynccontextmanager
from typing import TYPE_CHECKING, Generic

from nu.tree.node import _Node
from .type_vars import T_co


if TYPE_CHECKING:
    from collections.abc import AsyncIterator

    from ..context import Context


__all__ = [
    "LValue",
    "Nu",
    "RValue",
]


class Nu(_Node["Nu"], Generic[T_co]):  # noqa: UP046
    """The primitive. Recursive unit of computation.

    Everything is a Nu:
    - Literals (literal data)
    - Refs (pointers to locations)
    - Operations (transformations)

    Nus compose into trees. Trees evaluate within a Context.

    A bare Nu executes its children sequentially.
    Use ``|`` to compose horizontally: ``a | b | c``.
    """

    async def execute(self, ctx: Context) -> T_co:
        """Execute this Nu within a context.

        Default: execute children sequentially.
        """
        for child in self._children:
            await child.execute(ctx)

    @asynccontextmanager
    async def open(self, ctx: Context) -> AsyncIterator[T_co]:
        """Open this Nu as a live resource within a boundary.

        Default: execute and yield the result.
        Fabric Refs override to keep the boundary open for the lifetime
        of the context (e.g. Snapshot stays open while iterating a view).
        """
        yield await self.execute(ctx)

    @property
    def is_self_pure(self) -> bool:
        """Whether this Nu is pure (no side effects)."""
        return True

    @property
    def is_subtree_pure(self) -> bool:
        """Whether this Nu and its entire subtree are pure."""
        if not self.is_self_pure:
            return False
        return all(child.is_subtree_pure for child in self._children if isinstance(child, Nu))

    def __or__(self, other: object) -> Nu:
        """Compose sequentially: ``a | b`` executes a then b.

        Flattens when chained: ``a | b | c`` produces ``Nu(a, b, c)``.
        """
        if not isinstance(other, Nu):
            return NotImplemented  # type: ignore[return-value]
        if type(self) is Nu:
            return Nu(*self._children, other)
        return Nu(self, other)


class LValue(Nu[T_co], ABC):
    """Addressable location. Internal base for Ref."""


class RValue(Nu[T_co], ABC):
    """Evaluable expression. Internal base for Literal and Op."""
