"""Auto-wrap of non-Term children as Literal.

``Nu.__init__`` wraps any child that is not already a ``Term`` in a
``Literal`` so ``Add(1, 2)`` reads the same as
``Add(Literal(1), Literal(2))``. Every Python value is fair game --
ints, strings, ``None``, functions, even sentinels.
"""

from __future__ import annotations

from nu.core import Add, Literal
from nu.lang.helpers import run
from nu.lang.sentinels import EMPTY, INVALID


def test_int_child_is_wrapped() -> None:
    term = Add(1, 2)
    assert all(isinstance(c, Literal) for c in term._children)
    assert [c._payload["value"] for c in term._children] == [1, 2]


def test_term_child_is_left_alone() -> None:
    inner = Literal(7)
    term = Add(inner, 3)
    assert term._children[0] is inner
    assert isinstance(term._children[1], Literal)


def test_autowrap_runs_end_to_end() -> None:
    value, _ = run(Add(1, 2, 3))
    assert value == 6


def test_none_is_wrapped() -> None:
    term = Add(None)
    assert isinstance(term._children[0], Literal)
    assert term._children[0]._payload["value"] is None


def test_string_is_wrapped() -> None:
    term = Add("hi")
    assert term._children[0]._payload["value"] == "hi"


def test_callable_is_wrapped_as_value() -> None:
    def f() -> int:
        return 1

    term = Add(f)
    assert term._children[0]._payload["value"] is f


def test_sentinels_are_wrapped() -> None:
    term = Add(EMPTY, INVALID)
    assert all(isinstance(c, Literal) for c in term._children)
    assert term._children[0]._payload["value"] is EMPTY
    assert term._children[1]._payload["value"] is INVALID


def test_mixed_children_are_wrapped_individually() -> None:
    inner = Literal(10)
    term = Add(inner, 5, inner)
    assert term._children[0] is inner
    assert isinstance(term._children[1], Literal)
    assert term._children[2] is inner
