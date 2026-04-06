"""Nu - the primitive.

Nu is the recursive unit of computation. A Nu is made of Nus.
Both a leaf (Value(5)) and a full app are Nus.

Hierarchy:
    Nu[T_co]                - base: execute(context) -> T_co
    ├── LValue[T_co]        - addressable location (internal)
    │   └── Ref[T_co]       - typed pointer (see ref.py)
    └── RValue[T_co]        - evaluable expression (internal)
        ├── Value[T_co]     - literal/computed data (see value.py)
        └── Op[T_co]        - operation (see op.py)
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Generic

from .node import _Node
from .type_vars import T_co


if TYPE_CHECKING:
    from ..context import Context


__all__ = [
    "LValue",
    "Nu",
    "RValue",
]


class Nu(_Node["Nu"], Generic[T_co], ABC):  # noqa: UP046
    """The primitive. Recursive unit of computation.

    Everything is a Nu:
    - Values (literal data)
    - Refs (pointers to locations)
    - Operations (transformations)

    Nus compose into trees. Trees evaluate within a Context.
    """

    @abstractmethod
    async def execute(self, ctx: Context) -> T_co:
        """Execute this Nu within a context.

        Args:
            ctx: Runtime context with handles and resources.

        Returns:
            Nu-specific result.
        """
        ...

    @property
    @abstractmethod
    def is_self_pure(self) -> bool:
        """Whether this Nu is pure (no side effects)."""
        ...

    @property
    def is_subtree_pure(self) -> bool:
        """Whether this Nu and its entire subtree are pure."""
        if not self.is_self_pure:
            return False
        return all(child.is_subtree_pure for child in self._children if isinstance(child, Nu))


class LValue(Nu[T_co], ABC):
    """Addressable location. Internal base for Ref."""


class RValue(Nu[T_co], ABC):
    """Evaluable expression. Internal base for Value and Op."""
