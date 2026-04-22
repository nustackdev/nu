"""Command - imperative mutation. Contains WRITE in subtree. Yields nothing.

Taxonomy under Interaction:

    Command                   yields nothing; effect set contains WRITE
    ├── Atomic                terminal mutation; no inner Command. Hook: run / run_sync
    │   ├── NAryAtomic        auto-resolved operands, hook: apply / aapply
    │   │   ├── UnaryAtomic
    │   │   ├── BinaryAtomic
    │   │   └── TernaryAtomic
    └── Flow                  orchestrates inner Commands. Override open / open_sync

Atomic is the leaf pattern: override `run` / `run_sync`; base wraps to 0-yield.
NAryAtomic family mirrors NAryScalar for Atomic: resolve each child's first
yield (propagating sentinels), then call `apply(*values)` returning None.
Flow is the orchestrator pattern: override `open` / `open_sync` directly.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from contextlib import AsyncExitStack, ExitStack, aclosing, closing
from inspect import isawaitable, iscoroutinefunction
from typing import TYPE_CHECKING, Any

from .interaction import Interaction
from .types import Mode, is_sentinel


if TYPE_CHECKING:
    from collections.abc import AsyncGenerator, Generator

    from ..context import Context
    from .nu import Nu


__all__ = [
    "Atomic",
    "BinaryAtomic",
    "Command",
    "Flow",
    "NAryAtomic",
    "TernaryAtomic",
    "UnaryAtomic",
]


class Command(Interaction, ABC):
    """0-yield Interaction. Role marker.

    No abstract hook on the base: Atomic subclasses authoring via `run`
    declare their own abstract; Flow subclasses override `open` directly
    and leave `run` as the default raise.
    """

    async def run(self, ctx: Context) -> None:
        """Async side effect. Default raises; override or use open."""
        msg = f"{type(self).__name__} has no run; override run or open"
        raise NotImplementedError(msg)

    def run_sync(self, ctx: Context) -> None:
        """Sync side effect. Default raises; override or use open_sync."""
        msg = f"{type(self).__name__} has no run_sync; override run_sync or open_sync"
        raise NotImplementedError(msg)

    async def open(self, ctx: Context) -> AsyncGenerator[None, None]:
        await self.run(ctx)
        return
        yield  # unreachable; marks this as a generator

    def open_sync(self, ctx: Context) -> Generator[None, None, None]:
        if self.mode is Mode.ASYNC:
            msg = f"{type(self).__name__} is ASYNC-only; cannot run sync"
            raise RuntimeError(msg)
        self.run_sync(ctx)
        return
        yield  # unreachable


class Atomic(Command, ABC):
    """Terminal mutation. Leaf in the Command tree.

    Override `run(ctx)` for async or `run_sync(ctx)` for sync. No inner
    Command; children are all Queries (value to write, target Ref, etc).
    """

    @abstractmethod
    async def run(self, ctx: Context) -> None:
        """Perform the mutation. Called once."""
        ...


class Flow(Command, ABC):
    """Orchestrates inner Commands. Override `open` / `open_sync`.

    Children include Commands (body, branches) and Queries (control
    values). Flow doesn't use `run`; override `open` directly.
    """


# =============================================================================
# NARYATOMIC - operand-driven mutation with sentinel short-circuit
# =============================================================================


class NAryAtomic(Atomic, ABC):
    """Atomic with auto-resolved operands. Hook: apply(*values) / aapply(*values).

    Opens each child, takes the first yield, propagates EMPTY / INVALID
    (skips `apply` on sentinel — the mutation is aborted, nothing yielded).
    Calls `apply(*values)` once; `apply` returns None. Yields nothing.

    Use for Commands whose operands should be fully resolved before the
    side effect. For Commands that hold Ref targets (Store, Copy), stay on
    raw `Atomic` and manage resolution manually.
    """

    def __init__(self, *children: object) -> None:
        super().__init__(*children)

    def __repr__(self) -> str:
        args = ", ".join(repr(c) for c in self._children)
        return f"{self.__class__.__name__}({args})"

    def __str__(self) -> str:
        args = ", ".join(str(c) for c in self._children)
        return f"{self.__class__.__name__}({args})"

    async def run(self, ctx: Context) -> None:
        async with AsyncExitStack() as stack:
            values: list[Any] = []
            for child in self._children:
                gen = await stack.enter_async_context(aclosing(child.open(ctx)))
                try:
                    v = await gen.__anext__()
                except StopAsyncIteration:
                    return
                if is_sentinel(v):
                    return
                values.append(v)
            result = self.apply(*values)
            if isawaitable(result):
                await result

    def run_sync(self, ctx: Context) -> None:
        if self.mode is Mode.ASYNC:
            msg = f"{type(self).__name__} is ASYNC-only; cannot run sync"
            raise RuntimeError(msg)
        if iscoroutinefunction(self.apply):
            msg = f"{type(self).__name__}.apply is async; cannot run sync"
            raise RuntimeError(msg)
        with ExitStack() as stack:
            values: list[Any] = []
            for child in self._children:
                gen = stack.enter_context(closing(child.open_sync(ctx)))
                try:
                    v = next(gen)
                except StopIteration:
                    return
                if is_sentinel(v):
                    return
                values.append(v)
            self.apply(*values)

    @abstractmethod
    def apply(self, *values: Any) -> None:  # noqa: ANN401
        """Apply the mutation on resolved values. Sync or async; returns None."""
        ...


class UnaryAtomic(NAryAtomic, ABC):
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

    @abstractmethod
    def apply(self, operand: Any) -> None:  # type: ignore[override]  # noqa: ANN401
        ...


class BinaryAtomic(NAryAtomic, ABC):
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

    @abstractmethod
    def apply(self, left: Any, right: Any) -> None:  # type: ignore[override]  # noqa: ANN401
        ...


class TernaryAtomic(NAryAtomic, ABC):
    """Three operands."""

    def __init__(self, a: object, b: object, c: object) -> None:
        super().__init__(a, b, c)

    def __repr__(self) -> str:
        c0, c1, c2 = self._children
        return f"{self.__class__.__name__}({c0!r}, {c1!r}, {c2!r})"

    def __str__(self) -> str:
        c0, c1, c2 = self._children
        return f"{self.__class__.__name__}({c0}, {c1}, {c2})"

    @abstractmethod
    def apply(self, a: Any, b: Any, c: Any) -> None:  # type: ignore[override]  # noqa: ANN401
        ...
