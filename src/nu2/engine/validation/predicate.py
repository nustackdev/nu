"""Predicate: a composable ``(program, path) -> bool`` test.

Combine predicates with ``&``, ``|`` and ``~``; the right operand of a binary
combinator may be any bare callable of the same shape. Wrap a plain function
with the ``@predicate`` decorator to give it the same algebra.

Predicates are the building block for ``Law.scope`` and ``Law.holds``.
"""

from __future__ import annotations

from typing import TYPE_CHECKING


if TYPE_CHECKING:
    from collections.abc import Callable

    from nu2.engine.attribution.attributed_term import AttributedTerm, Path

__all__ = ["Predicate", "Test", "predicate"]

type Test = Callable[["AttributedTerm", "Path"], bool]


class Predicate:
    """A composable ``(program, path) -> bool`` test."""

    def __init__(self, test: Test) -> None:
        self._test = test
        self.__name__ = getattr(test, "__name__", "predicate")
        self.__doc__ = getattr(test, "__doc__", None)

    def __call__(self, program: AttributedTerm, path: Path) -> bool:
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
