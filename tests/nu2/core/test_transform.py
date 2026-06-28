"""Tests for the transform atoms (stream-to-stream lenses).

MapQuery and FilterQuery bind each item under a name (a child, default "item") and
evaluate a Nu child against it, read via AttrRef. SortedQuery / FlattenQuery / UniqueQuery are
single-source lenses. Coverage runs real programs through ``run``.
"""

from __future__ import annotations

from nu2.context import AttrRef
from nu2.core import CollectQuery, FilterQuery, IterQuery, LiteralQuery, LtQuery, MapQuery, MulQuery
from nu2.core.transform import FlattenQuery, SortedQuery, UniqueQuery
from nu2.lang import LAWS, Attr, Cardinality, compile, validate
from nu2.lang.helpers import run


# --- single-source lenses (SortedQuery / FlattenQuery / UniqueQuery) --------------------


def test_sorted_orders_its_source():
    value, _ = run(CollectQuery(SortedQuery(IterQuery(LiteralQuery([3, 1, 2])))))
    assert value == [1, 2, 3]


def test_flatten_concatenates_one_level():
    value, _ = run(CollectQuery(FlattenQuery(IterQuery(LiteralQuery([[1, 2], [3], [4, 5]])))))
    assert value == [1, 2, 3, 4, 5]


def test_unique_drops_repeats_first_seen_order():
    value, _ = run(CollectQuery(UniqueQuery(IterQuery(LiteralQuery([1, 2, 1, 3, 2])))))
    assert value == [1, 2, 3]


def test_a_single_source_lens_is_a_stream_and_validates():
    program = compile(SortedQuery(LiteralQuery([3, 1, 2])))
    assert program.attr(program.root, Attr.CARDINALITY) is Cardinality.STREAM
    assert validate(program, *LAWS) is program


# --- MapQuery -----------------------------------------------------------------


def test_map_is_a_stream():
    program = compile(
        MapQuery(IterQuery(LiteralQuery([1, 2, 3])), MulQuery(AttrRef("item"), LiteralQuery(10)))
    )
    assert program.attr(program.root, Attr.CARDINALITY) is Cardinality.STREAM


def test_map_applies_its_transform_per_item():
    tree = CollectQuery(
        MapQuery(IterQuery(LiteralQuery([1, 2, 3])), MulQuery(AttrRef("item"), LiteralQuery(10)))
    )
    value, _ = run(tree)
    assert value == [10, 20, 30]


def test_map_honors_a_custom_item_name():
    tree = CollectQuery(
        MapQuery(IterQuery(LiteralQuery([1, 2])), MulQuery(AttrRef("x"), LiteralQuery(2)), key="x")
    )
    value, _ = run(tree)
    assert value == [2, 4]


# --- FilterQuery --------------------------------------------------------------


def test_filter_keeps_matching_items():
    tree = CollectQuery(
        FilterQuery(
            IterQuery(LiteralQuery([1, 2, 3, 4])), LtQuery(AttrRef("item"), LiteralQuery(3))
        )
    )
    value, _ = run(tree)
    assert value == [1, 2]


# --- composition ---------------------------------------------------------


def test_a_lens_chain_stays_a_stream_and_evaluates():
    tree = CollectQuery(
        FilterQuery(
            MapQuery(
                IterQuery(LiteralQuery([1, 2, 3])), MulQuery(AttrRef("item"), LiteralQuery(10))
            ),
            LtQuery(AttrRef("item"), LiteralQuery(25)),
        )
    )
    program = compile(tree)
    assert validate(program, *LAWS) is program
    value, _ = run(tree)
    assert value == [10, 20]
