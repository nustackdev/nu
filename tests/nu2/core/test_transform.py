"""Tests for the transform atoms (stream-to-stream lenses).

Map and Filter bind each item under a name (a child, default "item") and
evaluate a Nu child against it, read via AttrRef. Coverage runs real programs
through ``run``. Sorted / Flatten / Unique are still structural stubs.
"""

from __future__ import annotations

import pytest

from nu2.context import AttrRef
from nu2.core import Collect, Filter, Iter, Literal, Lt, Map, Mul
from nu2.core.transform import Flatten, Sorted, Unique
from nu2.lang import LAWS, Attr, Cardinality, compile, validate
from nu2.lang.helpers import run


# --- structural stubs (Sorted / Flatten / Unique) ------------------------

STUBS = [Sorted, Flatten, Unique]


@pytest.mark.parametrize("atom", STUBS)
def test_stub_is_a_stream(atom):
    program = compile(atom(Literal([1, 2, 3])))
    assert program.attr(program.root, Attr.CARDINALITY) is Cardinality.STREAM


@pytest.mark.parametrize("atom", STUBS)
def test_stub_validates(atom):
    program = compile(atom(Literal([1, 2, 3])))
    assert validate(program, *LAWS) is program


# --- Map -----------------------------------------------------------------


def test_map_is_a_stream():
    program = compile(Map(Iter(Literal([1, 2, 3])), Mul(AttrRef("item"), Literal(10))))
    assert program.attr(program.root, Attr.CARDINALITY) is Cardinality.STREAM


def test_map_applies_its_transform_per_item():
    tree = Collect(Map(Iter(Literal([1, 2, 3])), Mul(AttrRef("item"), Literal(10))))
    value, _ = run(tree)
    assert value == [10, 20, 30]


def test_map_honors_a_custom_item_name():
    tree = Collect(Map(Iter(Literal([1, 2])), Mul(AttrRef("x"), Literal(2)), key="x"))
    value, _ = run(tree)
    assert value == [2, 4]


# --- Filter --------------------------------------------------------------


def test_filter_keeps_matching_items():
    tree = Collect(Filter(Iter(Literal([1, 2, 3, 4])), Lt(AttrRef("item"), Literal(3))))
    value, _ = run(tree)
    assert value == [1, 2]


# --- composition ---------------------------------------------------------


def test_a_lens_chain_stays_a_stream_and_evaluates():
    tree = Collect(
        Filter(
            Map(Iter(Literal([1, 2, 3])), Mul(AttrRef("item"), Literal(10))),
            Lt(AttrRef("item"), Literal(25)),
        )
    )
    program = compile(tree)
    assert validate(program, *LAWS) is program
    value, _ = run(tree)
    assert value == [10, 20]
