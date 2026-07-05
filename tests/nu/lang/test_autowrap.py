"""Auto-wrap of non-Term children as LiteralQuery.

``Nu.__init__`` wraps any child that is not already a ``Term`` in a
``LiteralQuery`` so ``AddQuery(1, 2)`` reads the same as
``AddQuery(LiteralQuery(1), LiteralQuery(2))``. Every Python value is fair game --
ints, strings, ``None``, functions, even sentinels.
"""

from __future__ import annotations

from nu.core import AddQuery, LiteralQuery
from nu.lang.helpers import run
from nu.lang.sentinels import EMPTY, INVALID


def test_int_child_is_wrapped() -> None:
    term = AddQuery(1, 2)
    assert all(isinstance(c, LiteralQuery) for c in term._children)
    assert [c._payload["value"] for c in term._children] == [1, 2]


def test_term_child_is_left_alone() -> None:
    inner = LiteralQuery(7)
    term = AddQuery(inner, 3)
    assert term._children[0] is inner
    assert isinstance(term._children[1], LiteralQuery)


def test_autowrap_runs_end_to_end() -> None:
    value, _ = run(AddQuery(1, 2, 3))
    assert value == 6


def test_none_is_wrapped() -> None:
    term = AddQuery(None)
    assert isinstance(term._children[0], LiteralQuery)
    assert term._children[0]._payload["value"] is None


def test_string_is_wrapped() -> None:
    term = AddQuery("hi")
    assert term._children[0]._payload["value"] == "hi"


def test_callable_is_wrapped_as_value() -> None:
    def f() -> int:
        return 1

    term = AddQuery(f)
    assert term._children[0]._payload["value"] is f


def test_sentinels_are_wrapped() -> None:
    term = AddQuery(EMPTY, INVALID)
    assert all(isinstance(c, LiteralQuery) for c in term._children)
    assert term._children[0]._payload["value"] is EMPTY
    assert term._children[1]._payload["value"] is INVALID


def test_mixed_children_are_wrapped_individually() -> None:
    inner = LiteralQuery(10)
    term = AddQuery(inner, 5, inner)
    assert term._children[0] is inner
    assert isinstance(term._children[1], LiteralQuery)
    assert term._children[2] is inner
