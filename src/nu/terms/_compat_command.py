"""Command - imperative mutation. Contains WRITE in subtree. Yields nothing.

Taxonomy under Interaction:

    Command                   yields nothing; effect set contains WRITE
    ├── Flow                  orchestrates inner Commands. Override open / aopen
    └── ScalarCommand         operand-driven mutation with sentinel propagation
        ├── UnaryCommand
        ├── BinaryCommand
        └── TernaryCommand

Flow is the orchestrator pattern: override `aopen` / `open` directly.
ScalarCommand is symmetric to ScalarQuery (see query.py) — same sentinel
propagation, same apply / aapply hook, same arity refinements — but the
hook returns None and the scope yields nothing.
"""

from __future__ import annotations

from abc import ABC
from contextlib import AsyncExitStack, ExitStack, aclosing, closing
from inspect import isawaitable, iscoroutinefunction
from typing import TYPE_CHECKING, Any

from ._compat_interaction import Interaction
from ._compat_types import Mode, is_sentinel


if TYPE_CHECKING:
    from collections.abc import AsyncGenerator, Generator

    from ..context import Context
    from ._compat_nu import Nu


__all__ = [
    "BinaryCommand",
    "Command",
    "Flow",
    "ScalarCommand",
    "TernaryCommand",
    "UnaryCommand",
]


# =============================================================================
# COMMAND BASE - 0-yield role marker
# =============================================================================


class Command(Interaction, ABC):
    """0-yield Interaction. Role marker.

    Base has non-abstract `arun` / `run` that raise by default. Two
    authoring patterns:

    - Override `arun(ctx)` or `run(ctx)`. The base's `aopen` / `open`
      wrap into a 0-yield generator.
    - Override `aopen` / `open` directly (for Flow-style orchestration).

    For operand-driven mutation with sentinel propagation, use
    `ScalarCommand` (and the arity refinements).
    """

    async def arun(self, ctx: Context) -> None:
        """Async side effect. Default delegates to sync `run`; override for async-only."""
        self.run(ctx)

    def run(self, ctx: Context) -> None:
        """Sync side effect. Default raises; override or use `open`."""
        msg = f"{type(self).__name__} has no run; override run or arun or open/aopen"
        raise NotImplementedError(msg)

    async def aopen(self, ctx: Context) -> AsyncGenerator[None, None]:
        await self.arun(ctx)
        return
        yield  # unreachable; marks this as a generator

    def open(self, ctx: Context) -> Generator[None, None, None]:
        if self.own_mode is Mode.ASYNC:
            msg = f"{type(self).__name__} is ASYNC-only; cannot run sync"
            raise RuntimeError(msg)
        self.run(ctx)
        return
        yield  # unreachable


# =============================================================================
# FLOW - orchestrator pattern
# =============================================================================


class Flow(Command, ABC):
    """Orchestrates inner Commands. Override `aopen` / `open` directly.

    Children include Commands (body, branches) and Queries (control
    values). Flow doesn't use `arun`; override `aopen` directly.
    """


# =============================================================================
# SCALAR - operand-driven mutation with sentinel propagation
# =============================================================================


class ScalarCommand(Command, ABC):
    """Command with auto-resolved operands. Hook: apply(*values) / aapply(*values).

    Opens each child, takes the first yield, propagates EMPTY / INVALID
    (skips `apply` on sentinel — the mutation is aborted, nothing yielded).
    Calls `apply(*values)` once; `apply` returns None. Yields nothing.

    Each child's generator stays suspended at its yield point via an exit
    stack — this keeps any scope the child opened (Snapshot, Atomic) alive
    through `apply`, so live views passed to `apply` still read from their
    backing context. Generators close LIFO on exit.

    Symmetric to `ScalarQuery` in query.py.
    """

    def __init__(self, *children: object) -> None:
        super().__init__(*children)

    def __repr__(self) -> str:
        args = ", ".join(repr(c) for c in self._children)
        return f"{self.__class__.__name__}({args})"

    def __str__(self) -> str:
        args = ", ".join(str(c) for c in self._children)
        return f"{self.__class__.__name__}({args})"

    async def arun(self, ctx: Context) -> None:
        async with AsyncExitStack() as stack:
            values: list[Any] = []
            for child in self._children:
                gen = await stack.enter_async_context(aclosing(child.aopen(ctx)))
                try:
                    v = await gen.__anext__()
                except StopAsyncIteration:
                    return
                if is_sentinel(v):
                    return
                values.append(v)
            # Prefer aapply if the subclass overrides it; otherwise fall back to apply.
            if type(self).aapply is not ScalarCommand.aapply:
                await self.aapply(*values)
            else:
                result = self.apply(*values)
                if isawaitable(result):
                    await result

    def run(self, ctx: Context) -> None:
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
                    return
                if is_sentinel(v):
                    return
                values.append(v)
            self.apply(*values)

    def apply(self, *values: Any) -> None:  # noqa: ANN401
        """Apply the mutation on resolved values (sync).

        Override this OR `aapply` (for async-only subclasses).
        """
        msg = f"{type(self).__name__} has no apply; override apply or aapply"
        raise NotImplementedError(msg)

    async def aapply(self, *values: Any) -> None:  # noqa: ANN401
        """Apply the mutation on resolved values (async).

        Default delegates to `apply`. Override for async-only subclasses.
        """
        self.apply(*values)


# =============================================================================
# ARITY REFINEMENTS
# =============================================================================


class UnaryCommand(ScalarCommand, ABC):
    """Single operand. For side effects on one resolved value."""

    def __init__(self, operand: object) -> None:
        super().__init__(operand)

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}({self.operand!r})"

    def __str__(self) -> str:
        return f"{self.__class__.__name__}({self.operand})"

    @property
    def operand(self) -> Nu:
        return self._children[0]


class BinaryCommand(ScalarCommand, ABC):
    """Two operands."""

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


class TernaryCommand(ScalarCommand, ABC):
    """Three operands."""

    def __init__(self, a: object, b: object, c: object) -> None:
        super().__init__(a, b, c)

    def __repr__(self) -> str:
        c0, c1, c2 = self._children
        return f"{self.__class__.__name__}({c0!r}, {c1!r}, {c2!r})"

    def __str__(self) -> str:
        c0, c1, c2 = self._children
        return f"{self.__class__.__name__}({c0}, {c1}, {c2})"
