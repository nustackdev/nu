"""Metaprogramming: laws over a compiled program, and the gate that runs them.

A Law is a declarative validity rule: a ``scope`` selecting the nodes it
judges, a ``holds`` predicate that must be true on each, a message, and a
severity. ``gate`` runs laws over every node and returns a verdict; ``validate``
turns an error-level verdict into a rejection. Nothing here mutates the program.

The attribute layer knows no sorts and no effects. A law's scope and holds are
opaque predicates; the language built on it supplies their meaning.
"""

from __future__ import annotations

from enum import StrEnum
from typing import TYPE_CHECKING, NamedTuple


if TYPE_CHECKING:
    from collections.abc import Callable

    from nu.attribute.program import Path, Program

__all__ = ["Law", "Predicate", "Severity", "Violation", "gate", "predicate", "validate"]


type Test = Callable[[Program, Path], bool]
type Message = str | Callable[[Program, Path], str]


class Severity(StrEnum):
    """How hard a law's failure bites: a rejection, or a flagged warning."""

    ERROR = "error"
    WARNING = "warning"


class Predicate:
    """A composable ``(program, path) -> bool`` test.

    Combine predicates with ``&``, ``|`` and ``~``; the right operand of a
    binary combinator may be any bare callable of the same shape. Wrap a plain
    function with the ``@predicate`` decorator to give it the same algebra.
    """

    def __init__(self, test: Test) -> None:
        self._test = test
        self.__name__ = getattr(test, "__name__", "predicate")
        self.__doc__ = getattr(test, "__doc__", None)

    def __call__(self, program: Program, path: Path) -> bool:
        """Run the test against ``path`` in ``program``."""
        return self._test(program, path)

    def __and__(self, other: Test) -> Predicate:
        return Predicate(lambda program, path: self(program, path) and other(program, path))

    def __or__(self, other: Test) -> Predicate:
        return Predicate(lambda program, path: self(program, path) or other(program, path))

    def __invert__(self) -> Predicate:
        return Predicate(lambda program, path: not self(program, path))

    def __repr__(self) -> str:
        return f"Predicate({self.__name__})"


def predicate(test: Test) -> Predicate:
    """Wrap a ``(program, path) -> bool`` function as a composable Predicate."""
    return Predicate(test)


class Violation(NamedTuple):
    """One law failure: where it is, which law, why, and how hard it bites."""

    path: Path
    law: str
    detail: str
    severity: Severity


class Law:
    """A declarative validity rule over the nodes of a compiled program.

    ``scope`` selects the nodes the law judges; ``holds`` is the predicate that
    must be true on each. When ``holds`` is false the law yields a Violation
    carrying ``message`` (a string, or a function of the node) at ``severity``.

    A law inspects only the attributes compilation produced. The folding that
    a subtree-wide check needs belongs in a synthesized attribute, so that the
    law itself stays a flat predicate over one node.
    """

    def __init__(
        self,
        name: str,
        *,
        scope: Test,
        holds: Test,
        message: Message,
        severity: Severity = Severity.ERROR,
    ) -> None:
        self.name = name
        self.scope = scope
        self.holds = holds
        self.message = message
        self.severity = severity

    def check(self, program: Program, path: Path) -> Violation | None:
        """The Violation this law yields at ``path``, or None if it holds."""
        if not self.scope(program, path) or self.holds(program, path):
            return None
        detail = self.message if isinstance(self.message, str) else self.message(program, path)
        return Violation(path, self.name, detail, self.severity)

    def __repr__(self) -> str:
        return f"Law({self.name!r})"


def gate(program: Program, *laws: Law) -> list[Violation]:
    """Run every law over every node and return every Violation found.

    The verdict is returned, never written onto the program.
    """
    return [
        violation
        for path in program.walk()
        for law in laws
        if (violation := law.check(program, path)) is not None
    ]


def validate(program: Program, *laws: Law) -> Program:
    """Run a gate; raise on any error-level Violation, else return the program.

    Warning-level violations pass through; read them with ``gate`` directly.

    Raises:
        ValueError: if any law yields an error-level Violation.
    """
    errors = [v for v in gate(program, *laws) if v.severity is Severity.ERROR]
    if errors:
        lines = "\n".join(f"  [{v.law}] {v.detail}  at {v.path}" for v in errors)
        raise ValueError(f"invalid program:\n{lines}")
    return program
