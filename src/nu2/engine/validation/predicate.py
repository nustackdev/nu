"""Predicate: a composable ``(program, path) -> bool`` test.

Two names appear here:

- ``Test`` is the callable *shape* -- any ``(program, path) -> bool``
  function. It is what laws ultimately consume; nothing more.
- ``Predicate`` wraps a ``Test`` to give it an *algebra*: ``&``, ``|``, and
  ``~`` combine predicates without forcing the caller to nest lambdas. The
  right operand of a binary combinator may be any bare ``Test`` -- the
  result is always a ``Predicate``.

Wrap a plain function with the ``@predicate`` decorator to give it the same
algebra. Predicates are the building block for ``Law.scope`` and
``Law.holds``.
"""

from __future__ import annotations

from typing import TYPE_CHECKING


if TYPE_CHECKING:
    from collections.abc import Callable

    from nu2.engine.compilation import Path, Program

__all__ = ["Predicate", "Test", "predicate"]

type Test = Callable[["Program", "Path"], bool]


class Predicate:
    """A composable ``(program, path) -> bool`` test."""

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
