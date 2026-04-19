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
        - open = resolve children via their `open` -> propagate sentinels -> apply()

    Lifecycle (resource scoping):
        - ScopedOp: before/after/after_failure hooks
        - open = before -> run children -> yield last value -> after/after_failure

Composition pattern:
    class AddOp(BinaryOp[float]):
        def apply(self, left: float, right: float) -> float:
            return left + right

Effect declarations (class-level):
    writes: int | tuple[int, ...] = ()
    reads:  int | tuple[int, ...] = ()

    class StoreOp(Op):
        writes = 0            # child 0 is a WRITE target

    class CopyOp(Op):
        reads  = 0
        writes = 1
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from contextlib import aclosing
from inspect import isawaitable
from typing import TYPE_CHECKING, Any, ClassVar

from .interaction import Interaction
from .sentinel import INVALID, Sentinel, is_sentinel
from .type_vars import T_co


if TYPE_CHECKING:
    from collections.abc import AsyncGenerator

    from ..context import Context
    from .nu import Nu


__all__ = [  # noqa: RUF022
    "Op",
    "NAryOp",
    "UnaryOp",
    "BinaryOp",
    "TernaryOp",
    "ScopedOp",
    "Command",
    "Query",
]


# =============================================================================
# OP BASE
# =============================================================================


class Op(Interaction[T_co], ABC):
    """Operation. Maps inputs to outputs.

    Effect tracking via class-level `writes` / `reads`:
    - `writes`: child positions that are WRITE targets.
    - `reads` : child positions that are READ targets.

    Accepts `int` (single position) or `tuple[int, ...]` (multiple).
    Un-listed Ref children default to READ in effect analysis.
    """

    writes: ClassVar[int | tuple[int, ...]] = ()
    reads: ClassVar[int | tuple[int, ...]] = ()

    def __init__(self, *children: object) -> None:
        """Initialize with operands. Python literals are wrapped into Literals."""
        from nu.utils import ensure_nu

        super().__init__(*[ensure_nu(c) for c in children])


# =============================================================================
# N-ARY OP WITH OPERAND MANAGEMENT
# =============================================================================


class NAryOp(Op[T_co | Sentinel], ABC):
    """Op with operands. Handles resolution and sentinels.

    Sentinel propagation:
        If any operand resolves to a sentinel (EMPTY, INVALID),
        the op yields INVALID without calling apply().
    """

    def __init__(self, *children: object) -> None:
        super().__init__(*children)

    def __repr__(self) -> str:
        args = ", ".join(repr(c) for c in self._children)
        return f"{self.__class__.__name__}({args})"

    def __str__(self) -> str:
        args = ", ".join(str(c) for c in self._children)
        return f"{self.__class__.__name__}({args})"

    async def open(self, ctx: Context) -> AsyncGenerator[T_co | Sentinel, None]:
        """Resolve each operand's stream (taking its last yield), apply, yield once.

        Opens each child as a generator, drains to the last value, propagates
        sentinels. `apply` may be sync or async; async results are awaited.
        Child exits run before `apply` in reverse order via aclosing.
        """
        values: list[Any] = []
        for child in self._children:
            v: Any = None
            async with aclosing(child.open(ctx)) as gen:
                async for x in gen:
                    v = x
            if is_sentinel(v):
                yield INVALID
                return
            values.append(v)
        result = self.apply(*values)
        if isawaitable(result):
            result = await result
        yield result

    @abstractmethod
    def apply(self, *values: Any) -> T_co | Sentinel:  # noqa: ANN401
        """Apply the transformation to resolved values. Sync or async."""
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
        return self._children[0]

    @abstractmethod
    def apply(self, operand: Any) -> T_co | Sentinel:  # type: ignore[override]  # noqa: ANN401
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
        return self._children[0]

    @property
    def right(self) -> Nu:
        return self._children[1]

    @abstractmethod
    def apply(self, left: Any, right: Any) -> T_co | Sentinel:  # type: ignore[override]  # noqa: ANN401
        ...


class TernaryOp(NAryOp[T_co], ABC):
    """Three operand op. For: if a then b else c, slice(a, b, c), etc.

    Children accessed via `self.children[0..2]`. Named per-position
    properties (first/second/third) were removed because they shadowed
    `Nu.first()` / `.last()` consumption helpers.
    """

    def __init__(self, a: object, b: object, c: object) -> None:
        super().__init__(a, b, c)

    def __repr__(self) -> str:
        c0, c1, c2 = self._children
        return f"{self.__class__.__name__}({c0!r}, {c1!r}, {c2!r})"

    def __str__(self) -> str:
        c0, c1, c2 = self._children
        return f"{self.__class__.__name__}({c0}, {c1}, {c2})"

    @abstractmethod
    def apply(self, a: Any, b: Any, c: Any) -> T_co | Sentinel:  # type: ignore[override]  # noqa: ANN401
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

    open(): forwards children's streams under the boundary; on exit, runs
    `after` or `after_failure` via generator finally.
    """

    async def open(self, ctx: Context) -> AsyncGenerator[Any, None]:
        """Enter boundary, stream children, commit/rollback on exit."""
        scoped_ctx = self.before(ctx)
        try:
            for child in self._children:
                async with aclosing(child.open(scoped_ctx)) as gen:
                    async for v in gen:
                        yield v
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


# =============================================================================
# COMMAND / QUERY MIXINS
# =============================================================================


class Command(Op, ABC):
    """Op that yields nothing (a Command in the Command/Query sense).

    Subclasses override `run(ctx)` and return None. The generator wrapping
    is handled here so authors don't deal with `if False: yield` tricks.

    Use for any Op whose semantics is pure side-effect on Γ:
    Store, Print, Log, StdioWrite, Assert (side-effect only), etc.
    """

    @abstractmethod
    async def run(self, ctx: Context) -> None:
        """Perform the side effect. No return value."""
        ...

    async def open(self, ctx: Context) -> AsyncGenerator[None, None]:
        await self.run(ctx)
        return
        yield  # unreachable; marks this as a generator


class Query(Op[T_co], ABC):
    """Op that yields exactly one value (a Query in the Command/Query sense).

    Subclasses override `run(ctx) -> T` and return a value. The generator
    wrapping is handled here; one `yield` of the computed value.

    Use when the Op needs raw `ctx` access and produces one value -
    e.g. reading `ctx.attrs[key]`, calling a method on `ctx.get(Service)`,
    or any custom-fetch pattern that isn't operand-apply.

    For pure compute from operands with sentinel propagation, use `NAryOp`
    (its `apply` now accepts async too).
    """

    @abstractmethod
    async def run(self, ctx: Context) -> T_co:
        """Compute the value. Called once; its return is the single yield."""
        ...

    async def open(self, ctx: Context) -> AsyncGenerator[T_co, None]:
        yield await self.run(ctx)
