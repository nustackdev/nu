"""Auto-wrap of non-Term children as Literal.

``Nu.__init__`` wraps any child that is not already a ``Term`` in a
``Literal`` so ``Add(1, 2)`` reads the same as
``Add(Literal(1), Literal(2))``. Every Python value is fair game --
ints, strings, ``None``, functions, even sentinels.
"""

from __future__ import annotations

import nu
from nu.core import Add
from nu.lang import Literal
from nu.lang.helpers import run
from nu.lang.sentinels import EMPTY


def test_int_child_is_wrapped() -> None:
    term = Add(1, 2)
    assert all(isinstance(c, Literal) for c in nu.tree.children(term))
    assert [nu.tree.payload(c)["value"] for c in nu.tree.children(term)] == [1, 2]


def test_term_child_is_left_alone() -> None:
    inner = Literal(7)
    term = Add(inner, 3)
    assert nu.tree.children(term)[0] is inner
    assert isinstance(nu.tree.children(term)[1], Literal)


def test_autowrap_runs_end_to_end() -> None:
    value, _ = run(Add(1, 2, 3))
    assert value == 6


def test_none_is_wrapped() -> None:
    term = Add(None)
    assert isinstance(nu.tree.children(term)[0], Literal)
    assert nu.tree.payload(nu.tree.children(term)[0])["value"] is None


def test_string_is_wrapped() -> None:
    term = Add("hi")
    assert nu.tree.payload(nu.tree.children(term)[0])["value"] == "hi"


def test_callable_is_wrapped_as_value() -> None:
    def f() -> int:
        return 1

    term = Add(f)
    assert nu.tree.payload(nu.tree.children(term)[0])["value"] is f


def test_empty_is_wrapped() -> None:
    term = Add(EMPTY, 1)
    assert all(isinstance(c, Literal) for c in nu.tree.children(term))
    assert nu.tree.payload(nu.tree.children(term)[0])["value"] is EMPTY


def test_mixed_children_are_wrapped_individually() -> None:
    inner = Literal(10)
    term = Add(inner, 5, inner)
    assert nu.tree.children(term)[0] is inner
    assert isinstance(nu.tree.children(term)[1], Literal)
    assert nu.tree.children(term)[2] is inner
