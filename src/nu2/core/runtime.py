"""Execution for the Nu core symbols.

A compiled Program carries the static facts; this runs it. A Context is the
mutable store a program reads and writes; the Interpreter walks the tree,
evaluating value-producing nodes and performing command effects.

Dispatch is a table keyed by kind, so the atom modules stay pure declarations.
Execution is synchronous: a Par runs its children in order, and async-only
kinds (Watch) are not runnable here.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from nu2.core import (
    Add,
    And,
    Count,
    Delete,
    Div,
    Emit,
    Eq,
    If,
    Literal,
    Lt,
    Max,
    Min,
    Mul,
    Neg,
    Not,
    Or,
    Par,
    Range,
    Retry,
    Scope,
    Seq,
    Set,
    Sub,
    Sum,
    While,
)
from nu2.lang import Ref


if TYPE_CHECKING:
    from collections.abc import Callable, Iterable

    from nu2.attribute import Program
    from nu2.attribute.program import Path

__all__ = ["Context", "Interpreter", "run"]


class Context:
    """The mutable store a Nu program reads and writes; Refs name its slots."""

    def __init__(self, **initial: object) -> None:
        self.store: dict[str, object] = dict(initial)

    def read(self, name: str) -> object:
        """The value bound to ``name``."""
        return self.store[name]

    def write(self, name: str, value: object) -> None:
        """Bind ``name`` to ``value``."""
        self.store[name] = value

    def __repr__(self) -> str:
        body = ", ".join(f"{k}={v!r}" for k, v in self.store.items())
        return f"Context({body})"


class Interpreter:
    """Walks a compiled Program: evaluates queries, runs commands and flows."""

    def __init__(self, program: Program, ctx: Context) -> None:
        self.program = program
        self.ctx = ctx

    def value(self, path: Path) -> object:
        """Evaluate a value-producing node to a Python value."""
        handler = _VALUE.get(self.program.kind(path))
        if handler is None:
            raise NotImplementedError(f"{self.program.kind(path).__name__} is not runnable")
        return handler(self, path)

    def run(self, path: Path) -> None:
        """Run a command or flow node for its effect on the Context."""
        handler = _RUN.get(self.program.kind(path))
        if handler is None:
            raise NotImplementedError(f"{self.program.kind(path).__name__} is not runnable")
        handler(self, path)

    def _kids(self, path: Path) -> list[Path]:
        return self.program.children(path)

    def _name(self, path: Path) -> str:
        return self.program.payload(path)["name"]


# --- value handlers: a node -> its Python value -----------------------------


def _ref(it: Interpreter, p: Path) -> object:
    return it.ctx.read(it._name(p))


def _literal(it: Interpreter, p: Path) -> object:
    return it.program.payload(p)["value"]


def _binary(op: Callable[[object, object], object]) -> Callable[[Interpreter, Path], object]:
    """A value handler for a two-child node."""

    def handler(it: Interpreter, p: Path) -> object:
        a, b = (it.value(c) for c in it._kids(p))
        return op(a, b)

    return handler


def _stream(it: Interpreter, p: Path) -> list:
    """The one stream child of a reduction, materialized."""
    (child,) = it._kids(p)
    return list(it.value(child))


def _product(values: Iterable[object]) -> object:
    """The product of an iterable, the multiplicative fold."""
    out = 1
    for v in values:
        out *= v
    return out


_VALUE = {
    Ref: _ref,
    Literal: _literal,
    Add: lambda it, p: sum(it.value(c) for c in it._kids(p)),
    Mul: lambda it, p: _product(it.value(c) for c in it._kids(p)),
    Sub: _binary(lambda a, b: a - b),
    Div: _binary(lambda a, b: a / b),
    Neg: lambda it, p: -it.value(it._kids(p)[0]),
    Eq: _binary(lambda a, b: a == b),
    Lt: _binary(lambda a, b: a < b),
    And: lambda it, p: all(it.value(c) for c in it._kids(p)),
    Or: lambda it, p: any(it.value(c) for c in it._kids(p)),
    Not: lambda it, p: not it.value(it._kids(p)[0]),
    Range: _binary(lambda lo, hi: list(range(lo, hi))),
    Sum: lambda it, p: sum(_stream(it, p)),
    Count: lambda it, p: len(_stream(it, p)),
    Max: lambda it, p: max(_stream(it, p)),
    Min: lambda it, p: min(_stream(it, p)),
}


# --- run handlers: a command or flow node -> its effect on the Context ------


def _set(it: Interpreter, p: Path) -> None:
    target, value = it._kids(p)
    it.ctx.write(it._name(target), it.value(value))


def _delete(it: Interpreter, p: Path) -> None:
    (target,) = it._kids(p)
    del it.ctx.store[it._name(target)]


def _emit(it: Interpreter, p: Path) -> None:
    target, value = it._kids(p)
    it.ctx.read(it._name(target)).append(it.value(value))


def _seq(it: Interpreter, p: Path) -> None:
    for child in it._kids(p):
        it.run(child)


def _if(it: Interpreter, p: Path) -> None:
    condition, *body = it._kids(p)
    if it.value(condition):
        for child in body:
            it.run(child)


def _while(it: Interpreter, p: Path) -> None:
    condition, *body = it._kids(p)
    while it.value(condition):
        for child in body:
            it.run(child)


def _body(it: Interpreter, p: Path) -> None:
    for child in it._kids(p):
        it.run(child)


def _retry(it: Interpreter, p: Path) -> None:
    limit: int = it.program.payload(p).get("limit", 1)
    for attempt in range(limit + 1):
        try:
            _body(it, p)
            return
        except Exception:
            if attempt == limit:
                raise


_RUN = {
    Set: _set,
    Delete: _delete,
    Emit: _emit,
    Seq: _seq,
    Par: _seq,
    If: _if,
    While: _while,
    Scope: _body,
    Retry: _retry,
}


def run(program: Program, ctx: Context | None = None) -> Context:
    """Run a compiled command-or-flow program; return the Context it left.

    Args:
        program: a compiled Program whose root is a Command or Flow.
        ctx: the store to run against; a fresh empty Context by default.

    Returns:
        The Context after the program's effects.
    """
    ctx = ctx if ctx is not None else Context()
    Interpreter(program, ctx).run(program.root)
    return ctx
