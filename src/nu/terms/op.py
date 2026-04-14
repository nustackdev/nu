"""Op - operation hierarchy.

Operations transform inputs to outputs:

    Nu                          - the primitive
    └── RValue                  - evaluable expression
        └── Interaction         - evaluable computation
            └── Op              - operation (maps inputs to outputs)
                └── NAryOp      - op with operands and sentinel handling
                    ├── UnaryOp     - single operand
                    ├── BinaryOp    - two operands
                    └── TernaryOp   - three operands

Two dimensions:

    Arity (how many operands):
        - NAryOp, UnaryOp, BinaryOp, TernaryOp
        - execute = resolve children -> propagate sentinels -> apply()

    Lifecycle (resource scoping):
        - ScopedOp: before/after/after_failure hooks
        - execute = before(ctx) -> run children sequentially -> after/after_failure

Composition pattern:
    class AddOp(BinaryOp[float]):
        def apply(self, left: float, right: float) -> float:
            return left + right
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from contextlib import asynccontextmanager
from typing import TYPE_CHECKING, Any, ClassVar

from .interaction import Interaction
from .nu import Nu
from .sentinel import INVALID, Sentinel, is_sentinel
from .type_vars import T_co


if TYPE_CHECKING:
    from collections.abc import AsyncIterator

    from ..context import Context
    from .effect import Direction


__all__ = [  # noqa: RUF022
    # Base
    "Op",
    "NAryOp",
    "UnaryOp",
    "BinaryOp",
    "TernaryOp",
    # Lifecycle
    "ScopedOp",
]


# =============================================================================
# OP BASE
# =============================================================================


class Op(Interaction[T_co], ABC):
    """Operation. Maps inputs to outputs.

    Ops are the fundamental unit of computation:
    - UnaryOp: single operand (-x, abs(x), not x)
    - BinaryOp: two operands (x + y, x > y)
    - TernaryOp: three operands (if a then b else c)

    Extend NAryOp for operand-based ops with sentinel propagation.
    Extend ScopedOp for resource lifecycle (before/after hooks).
    Extend Op directly for custom execution.

    Effect tracking:
        overrides maps child position to Direction for effect analysis.
        Default empty = all children use default rules (Ref -> READ).
    """

    overrides: ClassVar[dict[int, Direction]] = {}

    def __init__(self, *children: object) -> None:
        """Initialize with operands. Python literals are wrapped into Values."""
        # FIXME: This is a core circular dependency!!
        from nu.utils import ensure_nu

        super().__init__(*[ensure_nu(c) for c in children])


# =============================================================================
# N-ARY OP WITH OPERAND MANAGEMENT
# =============================================================================


class NAryOp(Op[T_co | Sentinel], ABC):
    """Op with operands. Handles resolution and sentinels.

    Subclasses with fixed arity should use UnaryOp, BinaryOp, or
    TernaryOp. Subclasses with variable arity can override __init__.

    Sentinel propagation:
        If any operand resolves to a sentinel (EMPTY, INVALID),
        the op returns INVALID without calling apply().
    """

    def __init__(self, *children: object) -> None:
        """Initialize with operands."""
        super().__init__(*children)

    def __repr__(self) -> str:
        args = ", ".join(repr(c) for c in self._children)
        return f"{self.__class__.__name__}({args})"

    def __str__(self) -> str:
        args = ", ".join(str(c) for c in self._children)
        return f"{self.__class__.__name__}({args})"

    # =========================================================================
    # EXECUTION
    # =========================================================================

    async def execute(self, ctx: Context) -> T_co | Sentinel:
        """Resolve operands via open() to keep boundaries alive, then apply."""
        from contextlib import AsyncExitStack

        async with AsyncExitStack() as stack:
            values = []
            for child in self.children:
                val = await stack.enter_async_context(child.open(ctx))
                if is_sentinel(val):
                    return INVALID
                values.append(val)
            return self.apply(*values)

    @asynccontextmanager
    async def open(self, ctx: Context) -> AsyncIterator[T_co | Sentinel]:
        """Like execute but keeps child boundaries alive via open() chain."""
        # Use contextlib.AsyncExitStack to nest all children's open() contexts
        from contextlib import AsyncExitStack

        async with AsyncExitStack() as stack:
            values = []
            for child in self.children:
                val = await stack.enter_async_context(child.open(ctx))
                if is_sentinel(val):
                    yield INVALID
                    return
                values.append(val)
            yield self.apply(*values)

    @abstractmethod
    def apply(self, *values: Any) -> T_co | Sentinel:  # noqa: ANN401
        """Apply the transformation to resolved values.

        Called after all operands are resolved and verified non-sentinel.

        Args:
            *values: Resolved operand values (never sentinels)

        Returns:
            Result of the transformation
        """
        ...


# =============================================================================
# ARITY-SPECIFIC OPS
# =============================================================================


class UnaryOp(NAryOp[T_co], ABC):
    """Single operand op. For: -x, abs(x), not x, len(x), etc."""

    def __init__(self, operand: object) -> None:
        super().__init__(operand)

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}({self.operand!r})"

    def __str__(self) -> str:
        return f"{self.__class__.__name__}({self.operand})"

    @property
    def operand(self) -> Nu:
        """The single operand."""
        return self._children[0]

    @abstractmethod
    def apply(self, operand: Any) -> T_co | Sentinel:  # type: ignore[override]  # noqa: ANN401
        """Apply."""
        ...


class BinaryOp(NAryOp[T_co], ABC):
    """Two operand op. For: x + y, x > y, x and y, x[y], etc."""

    def __init__(self, left: object, right: object) -> None:
        super().__init__(left, right)

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}({self.left!r}, {self.right!r})"

    def __str__(self) -> str:
        return f"{self.__class__.__name__}({self.left}, {self.right})"

    @property
    def left(self) -> Nu:
        """Left operand."""
        return self._children[0]

    @property
    def right(self) -> Nu:
        """Right operand."""
        return self._children[1]

    @abstractmethod
    def apply(self, left: Any, right: Any) -> T_co | Sentinel:  # type: ignore[override]  # noqa: ANN401
        """Apply."""
        ...


class TernaryOp(NAryOp[T_co], ABC):
    """Three operand op. For: if a then b else c, slice(a, b, c), etc."""

    def __init__(self, first: object, second: object, third: object) -> None:
        super().__init__(first, second, third)

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}({self.first!r}, {self.second!r}, {self.third!r})"

    def __str__(self) -> str:
        return f"{self.__class__.__name__}({self.first}, {self.second}, {self.third})"

    @property
    def first(self) -> Nu:
        """First operand."""
        return self._children[0]

    @property
    def second(self) -> Nu:
        """Second operand."""
        return self._children[1]

    @property
    def third(self) -> Nu:
        """Third operand."""
        return self._children[2]

    @abstractmethod
    def apply(self, first: Any, second: Any, third: Any) -> T_co | Sentinel:  # type: ignore[override]  # noqa: ANN401
        """Apply."""
        ...


# =============================================================================
# LIFECYCLE
# =============================================================================


class ScopedOp(Op, ABC):
    """Op with resource lifecycle hooks.

    Scoped ops run children sequentially within a before/after boundary.
    Override hooks to scope context, manage resources, or add instrumentation.

    Hooks:
        before(ctx) -> ctx:          Set up resources, return scoped context.
        after(ctx):                  Clean up after successful execution.
        after_failure(ctx, error):   Clean up after failed execution.

    execute() returns the last child's value.
    open() yields the scoped context, keeping the boundary alive.
    """

    async def execute(self, ctx: Context) -> object:
        """Execute with lifecycle: before -> run children -> after/after_failure.

        Returns the last child's value.
        """
        scoped_ctx = self.before(ctx)
        result = None
        try:
            for child in self.children:
                result = await child.execute(scoped_ctx)
            self.after(scoped_ctx)
            return result
        except BaseException as e:
            self.after_failure(scoped_ctx, e)
            raise

    @asynccontextmanager
    async def open(self, ctx: Context) -> AsyncIterator:
        """Open boundary, run children, yield last child's value, close on exit."""
        scoped_ctx = self.before(ctx)
        result = None
        try:
            for child in self.children:
                result = await child.execute(scoped_ctx)
            yield result
            self.after(scoped_ctx)
        except BaseException as e:
            self.after_failure(scoped_ctx, e)
            raise

    def before(self, ctx: Context) -> Context:
        """Set up resources, return scoped context for children."""
        return ctx

    def after(self, ctx: Context) -> None:
        """Clean up after successful execution."""

    def after_failure(self, ctx: Context, error: BaseException) -> None:
        """Clean up after failed execution."""
