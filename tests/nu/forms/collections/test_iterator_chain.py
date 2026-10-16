"""Iterator chain methods: a stream chain ends in a fold or stays a stream.

Each method is sugar over one core atom. Every case checks the tree it builds
(the atom under the returned form), the value it yields sync and async, and
that an empty stream yields what the atom yields on its own.
"""

from __future__ import annotations

import asyncio

import pytest

import nu
from nu.core import (
    AllOf,
    AnyOf,
    Collect,
    Count,
    Enumerate,
    Flatten,
    Last,
    Max,
    Min,
    Reversed,
    SortBy,
    Sorted,
    Sum,
    Unique,
    Zip,
)
from nu.forms import Bool, Int, Iterator, List, Object
from nu.lang import EMPTY
from nu.lang.helpers import arun, run


def _both(term: object) -> object:
    """The value ``term`` yields, asserted equal under sync and async."""
    sync = run(term)[0]
    asynced = asyncio.run(arun(term))[0]
    assert sync == asynced or (sync is EMPTY and asynced is EMPTY)
    return sync


def _atom(form: object) -> object:
    (atom,) = nu.tree.children(form)
    return atom


def _stream(*items: object) -> Iterator:
    return nu.List.of(*items).iter()


# --- folds: stream to one value ---------------------------------------------

FOLDS = [
    # (method, args, atom, form, items, value, empty value)
    ("count", (), Count, Int, (1, 2, 3), 3, 0),
    ("sum", (), Sum, Object, (1, 2, 3), 6, 0),
    ("min", (), Min, Object, (3, 1, 2), 1, EMPTY),
    ("max", (), Max, Object, (3, 1, 2), 3, EMPTY),
    ("any", (), AnyOf, Bool, (0, 0, 1), True, False),
    ("all", (), AllOf, Bool, (1, 1, 0), False, True),
    ("last", (), Last, Object, (1, 2, 3), 3, EMPTY),
]


@pytest.mark.parametrize(("method", "args", "atom", "form", "items", "value", "empty"), FOLDS)
def test_a_fold_builds_its_atom_under_the_scalar_form(
    method, args, atom, form, items, value, empty
):
    result = getattr(_stream(*items), method)(*args)
    assert type(result) is form
    assert type(_atom(result)) is atom


@pytest.mark.parametrize(("method", "args", "atom", "form", "items", "value", "empty"), FOLDS)
def test_a_fold_yields_the_atoms_value(method, args, atom, form, items, value, empty):
    assert _both(getattr(_stream(*items), method)(*args)) == value
    assert _both(atom(nu.Iter(list(items)))) == value


@pytest.mark.parametrize(("method", "args", "atom", "form", "items", "value", "empty"), FOLDS)
def test_a_fold_over_an_empty_stream_matches_the_atom(
    method, args, atom, form, items, value, empty
):
    got = _both(getattr(_stream(), method)(*args))
    bare = _both(atom(nu.Iter([])))
    if empty is EMPTY:
        assert got is EMPTY
        assert bare is EMPTY
    else:
        assert got == bare == empty


def test_a_fold_keeps_chaining():
    xs = _stream(1, 2, 3, 4)
    assert _both(xs.filter(lambda x: x > 1).sum() > 5) is True
    assert _both(xs.count() + 1) == 5
    assert _both(xs.map(lambda x: nu.Int(x) > 3).any().not_()) is False
    assert _both(xs.max() - xs.min()) == 3


# --- stream to stream ---------------------------------------------------------

STREAMS = [
    # (build, atom, items, value, empty value)
    (lambda s: s.unique(), Unique, (1, 2, 1, 3), [1, 2, 3], []),
    (lambda s: s.reversed(), Reversed, (1, 2, 3), [3, 2, 1], []),
    (lambda s: s.sort_by(lambda x: -nu.Int(x)), SortBy, (2, 3, 1), [3, 2, 1], []),
    (lambda s: s.sort_by(nu.context.Attr("item"), reverse=True), SortBy, (2, 3, 1), [3, 2, 1], []),
    (lambda s: s.enumerate(), Enumerate, ("a", "b"), [(0, "a"), (1, "b")], []),
    (lambda s: s.enumerate(5), Enumerate, ("a",), [(5, "a")], []),
    (lambda s: s.zip(_stream("x", "y")), Zip, (1, 2, 3), [(1, "x"), (2, "y")], []),
    (lambda s: s.flatten(), Flatten, ([1, 2], [3]), [1, 2, 3], []),
]


@pytest.mark.parametrize(("build", "atom", "items", "value", "empty"), STREAMS)
def test_a_stream_op_builds_its_atom_and_stays_an_iterator(build, atom, items, value, empty):
    result = build(_stream(*items))
    assert type(result) is Iterator
    assert type(_atom(result)) is atom


@pytest.mark.parametrize(("build", "atom", "items", "value", "empty"), STREAMS)
def test_a_stream_op_yields_the_atoms_items(build, atom, items, value, empty):
    assert _both(build(_stream(*items)).to_list()) == value
    assert _both(build(_stream()).to_list()) == empty


def test_stream_ops_chain_into_a_fold():
    xs = _stream(3, 1, 3, 2)
    assert _both(xs.unique().sort_by(lambda x: nu.Int(x)).last()) == 3
    assert _both(xs.enumerate().count()) == 4


# --- sorted: drained into a List ----------------------------------------------


def test_sorted_builds_sorted_over_collect_as_a_list():
    result = _stream(3, 1, 2).sorted()
    assert type(result) is List
    atom = _atom(result)
    assert type(atom) is Sorted
    assert type(_atom(atom)) is Collect


def test_sorted_yields_an_ascending_list_and_empty_for_empty():
    assert _both(_stream(3, 1, 2).sorted()) == [1, 2, 3]
    assert _both(_stream().sorted()) == []
    assert _both(_stream(3, 1, 2).sorted().first_elem()) == 1
