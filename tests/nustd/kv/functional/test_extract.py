"""Core ``Extract`` over a kv ref wrapped in a concrete form yields plain data.

A kv container reads as a live view. The views are registered with core
``Extractable``, so ``nu.Dict(ref).extract()`` asks the view for its data
instead of handing the view out, on either facet.
"""

from __future__ import annotations

import pytest

import nu
from nu import run
from nu.domains.shape import Extractable, Shape
from nustd.kv import DictRef, Kh57Ref, ListRef, LogDictRef, OrderedDictRef, SetRef, StrRef


class Row(Shape):
    sym = StrRef.slot()


class Bag(Shape):
    names = DictRef.slot(str)
    rows = DictRef.slot(Row)
    ordered = OrderedDictRef.slot(int)
    logged = LogDictRef.slot(int)
    points = Kh57Ref.slot(int)
    tags = ListRef.slot(str)
    members = SetRef.slot(str)


CASES = {
    "dict": (Bag.names, nu.Dict, {"a": "x"}),
    "nested dict": (Bag.rows, nu.Dict, {"r": {"sym": "SOL"}}),
    "ordered dict": (Bag.ordered, nu.Dict, {"a": 1}),
    "log dict": (Bag.logged, nu.Dict, {"a": 1}),
    "kh57": (Bag.points, nu.Dict, {7: 1}),
    "list": (Bag.tags, nu.List, ["x", "y"]),
    "set": (Bag.members, nu.Set, {"x"}),
}


@pytest.mark.parametrize("name", CASES)
@pytest.mark.parametrize("facet", ["lazy", "eager"])
def test_extract_through_a_concrete_form_is_plain_data(ctx, name, facet) -> None:
    ref, form, value = CASES[name]
    run(ref.set(value), ctx)
    got = run(form(getattr(ref, facet)).extract(), ctx)[0]
    assert not isinstance(got, Extractable)
    assert got == value
    assert type(got) is type(value)


def test_the_view_a_ref_reads_is_extractable(ctx) -> None:
    run(Bag.names.set({"a": "x"}), ctx)
    assert isinstance(run(Bag.names, ctx)[0], Extractable)
