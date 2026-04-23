"""Query - functional construction. Yields value(s). No observable mutation.

Taxonomy under Interaction:

    Query[T]                  yields value(s); effect set ⊆ {CALC, RESOLVE, READ}
    ├── Literal[T]            trivial leaf: holds a value, yields it once
    ├── Stream[T]             N yields; author overrides open / aopen
    └── ScalarQuery[T]        operand-driven compute with sentinel propagation
        ├── UnaryQuery[T]
        ├── BinaryQuery[T]
        └── TernaryQuery[T]

Stream is the multi-yield pattern: override `aopen` / `open` directly.
ScalarQuery is symmetric to ScalarCommand (see command.py) — same sentinel
propagation, same apply / aapply hook, same arity refinements — but the
hook returns T and the scope yields once.

Command children are forbidden anywhere in a Query subtree (purity is global).
"""

from __future__ import annotations

from abc import ABC
from contextlib import AsyncExitStack, ExitStack, aclosing, closing
from inspect import isawaitable, iscoroutinefunction
from typing import TYPE_CHECKING, Any, ClassVar

from .interaction import Interaction
from .types import INVALID, Mode, Sentinel, T_co, is_sentinel


if TYPE_CHECKING:
    from collections.abc import AsyncGenerator, Generator

    from ..context import Context
    from .nu import Nu


__all__ = [
    "BinaryQuery",
    "Literal",
    "Query",
    "ScalarQuery",
    "Stream",
    "TernaryQuery",
    "UnaryQuery",
]


# =============================================================================
# QUERY BASE - 1-yield sugar
# =============================================================================


class Query(Interaction[T_co], ABC):
    """Functional-role Interaction. No observable mutation; yields value(s).

    Base has non-abstract `arun` / `run` that raise by default. Two
    authoring patterns:

    - 1-yield sugar: override `arun(ctx) -> T` (async) or `run(ctx) -> T`
      (sync). The base's `aopen` / `open` wrap into a 1-yield generator.
    - Override `aopen` / `open` directly (for N-yield streaming or
      apply-style compute). Leave `arun` as the default raise.

    For operand-driven compute with sentinel propagation, use `ScalarQuery`
    (and the arity refinements). For N-yield streams, use `Stream`.
    """

    async def arun(self, ctx: Context) -> T_co:
        """Async compute. Default delegates to sync `run`; override for async-only."""
        return self.run(ctx)

    def run(self, ctx: Context) -> T_co:
        """Sync compute. Default raises; override or use `open`."""
        msg = f"{type(self).__name__} has no run; override run or arun or open/aopen"
        raise NotImplementedError(msg)

    async def aopen(self, ctx: Context) -> AsyncGenerator[T_co, None]:
        yield await self.arun(ctx)

    def open(self, ctx: Context) -> Generator[T_co, None, None]:
        if self.own_mode is Mode.ASYNC:
            msg = f"{type(self).__name__} is ASYNC-only; cannot run sync"
            raise RuntimeError(msg)
        yield self.run(ctx)


# =============================================================================
# LITERAL - trivial leaf Query
# =============================================================================


class Literal(Query[T_co]):
    """Irreducible leaf. Holds a value, yields it once. No children.

    A trivial scalar Query. Bypasses the Query hook machinery: the stored
    value IS the yield.
    """

    own_mode: ClassVar[Mode] = Mode.BOTH
    func_mode: ClassVar[Mode] = Mode.SYNC

    _value: object

    def __init__(self, value: T_co) -> None:
        super().__init__()  # no children
        self._value = value

    async def aopen(self, ctx: Context) -> AsyncGenerator[T_co, None]:
        yield self._value  # type: ignore[misc]

    def open(self, ctx: Context) -> Generator[T_co, None, None]:
        yield self._value  # type: ignore[misc]

    @property
    def is_self_pure(self) -> bool:
        return True

    def __repr__(self) -> str:
        return f"Literal({self._value!r})"


# =============================================================================
# SCALAR - operand-driven compute with sentinel propagation
# =============================================================================


class ScalarQuery(Query[T_co | Sentinel], ABC):
    """Query with auto-resolved operands. Hook: apply(*values) / aapply(*values).

    Opens each child, takes the first yield, propagates EMPTY / INVALID
    (yields INVALID without calling apply), calls apply, yields once.

    Each child's generator stays suspended at its yield point via an exit
    stack — this keeps any scope the child opened (Snapshot, Atomic) alive
    through `apply`, so live views passed to `apply` still read from their
    backing context. Generators close LIFO on exit.

    Symmetric to `ScalarCommand` in command.py.
    """

    def __init__(self, *children: object) -> None:
        super().__init__(*children)

    def __repr__(self) -> str:
        args = ", ".join(repr(c) for c in self._children)
        return f"{self.__class__.__name__}({args})"

    def __str__(self) -> str:
        args = ", ".join(str(c) for c in self._children)
        return f"{self.__class__.__name__}({args})"

    async def aopen(self, ctx: Context) -> AsyncGenerator[T_co | Sentinel, None]:
        async with AsyncExitStack() as stack:
            values: list[Any] = []
            for child in self._children:
                gen = await stack.enter_async_context(aclosing(child.aopen(ctx)))
                try:
                    v = await gen.__anext__()
                except StopAsyncIteration:
                    yield INVALID
                    return
                if is_sentinel(v):
                    yield INVALID
                    return
                values.append(v)
            # Prefer aapply if the subclass overrides it; otherwise fall back to apply.
            if type(self).aapply is not ScalarQuery.aapply:
                result = await self.aapply(*values)
            else:
                result = self.apply(*values)
                if isawaitable(result):
                    result = await result
            yield result

    def open(self, ctx: Context) -> Generator[T_co | Sentinel, None, None]:
        if self.own_mode is Mode.ASYNC:
            msg = f"{type(self).__name__} is ASYNC-only; cannot run sync"
            raise RuntimeError(msg)
        if iscoroutinefunction(self.apply):
            msg = f"{type(self).__name__}.apply is async; cannot run sync"
            raise RuntimeError(msg)
        with ExitStack() as stack:
            values: list[Any] = []
            for child in self._children:
                gen = stack.enter_context(closing(child.open(ctx)))
                try:
                    v = next(gen)
                except StopIteration:
                    yield INVALID
                    return
                if is_sentinel(v):
                    yield INVALID
                    return
                values.append(v)
            yield self.apply(*values)

    def apply(self, *values: Any) -> T_co | Sentinel:  # noqa: ANN401
        """Apply the transformation on resolved values (sync).

        Override this OR `aapply` (for async-only subclasses).
        """
        msg = f"{type(self).__name__} has no apply; override apply or aapply"
        raise NotImplementedError(msg)

    async def aapply(self, *values: Any) -> T_co | Sentinel:  # noqa: ANN401
        """Apply the transformation on resolved values (async).

        Default delegates to `apply`. Override for async-only subclasses.
        """
        return self.apply(*values)


# =============================================================================
# ARITY REFINEMENTS
# =============================================================================


class UnaryQuery(ScalarQuery[T_co], ABC):
    """Single operand. For: -x, abs(x), not x, len(x), etc."""

    def __init__(self, operand: object) -> None:
        super().__init__(operand)

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}({self.operand!r})"

    def __str__(self) -> str:
        return f"{self.__class__.__name__}({self.operand})"

    @property
    def operand(self) -> Nu:
        return self._children[0]


class BinaryQuery(ScalarQuery[T_co], ABC):
    """Two operands. For: x + y, x > y, x and y, x[y], etc."""

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


class TernaryQuery(ScalarQuery[T_co], ABC):
    """Three operands. Children accessed via self.children[0..2]."""

    def __init__(self, a: object, b: object, c: object) -> None:
        super().__init__(a, b, c)

    def __repr__(self) -> str:
        c0, c1, c2 = self._children
        return f"{self.__class__.__name__}({c0!r}, {c1!r}, {c2!r})"

    def __str__(self) -> str:
        c0, c1, c2 = self._children
        return f"{self.__class__.__name__}({c0}, {c1}, {c2})"


# =============================================================================
# STREAM - multi-yield Query
# =============================================================================


class Stream(Query[T_co], ABC):
    """N-yield Query. Author overrides open / aopen directly.

    Use for streaming value producers: Map, Filter, Take, Subscribe,
    and any multi-yield Query whose shape doesn't fit the 1-yield sugar.

    No hook; override open / aopen. Still a Query by role (no WRITE in
    subtree). Composes inside other Queries and Commands like any Query.
    """
