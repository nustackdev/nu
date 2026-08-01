"""Dedicated functional tests for mem Ref *composition* — the hard cases.

The other mem suites cover single-hop CRUD and collection views. This file
targets what the ref redesign is actually about: deep hierarchical navigation,
write-path vivification, dynamic keys, and refs-used-as-keys (refs inside refs).
All against a real Python dict bound in the Context — no mocks.

Layout under test: parent lives at ``children[0]`` (structural), the address at
``children[1]``. These tests pin that the parent-on-tree wiring resolves,
writes, vivifies, and reads back correctly through several levels and with
dynamic / ref-valued keys.
"""

from __future__ import annotations

import pytest

from nu import Context, run
from nu.domains.shape import Shape
from nu.mem import IntRef, ShapeRef, ShapesDictRef, ShapesListRef, StrRef


# --- shapes: a genuine 3-level hierarchy ------------------------------------


class Inner(Shape):
    label = StrRef.slot()
    count = IntRef.slot()


class Mid(Shape):
    inners = ShapesDictRef.slot(Inner)
    note = StrRef.slot()


class Root(Shape):
    mids = ShapesDictRef.slot(Mid)
    rows = ShapesListRef.slot(Inner)
    info = ShapeRef.slot(Inner)
    active = StrRef.slot()  # holds a key; used as a dynamic / ref-valued key


@pytest.fixture
def data() -> dict:
    return {}


@pytest.fixture
def ctx(data: dict) -> Context:
    return Context().bind(dict, data, Root)


# --- deep navigation: read -------------------------------------------------


def test_three_deep_read(ctx, data):
    data["mids"] = {"m1": {"inners": {"i1": {"label": "hello"}}}}
    assert run(Root.mids["m1"].inners["i1"].label, ctx)[0] == "hello"


def test_three_deep_read_sibling_leaf(ctx, data):
    data["mids"] = {"m1": {"inners": {"i1": {"label": "hi", "count": 7}}}}
    assert run(Root.mids["m1"].inners["i1"].count, ctx)[0] == 7


# --- deep navigation: write + vivification ---------------------------------


def test_three_deep_vivification_into_empty(ctx, data):
    run(Root.mids["m1"].inners["i1"].label.set("deep"), ctx)
    assert data == {"mids": {"m1": {"inners": {"i1": {"label": "deep"}}}}}


def test_three_deep_write_then_read(ctx):
    run(Root.mids["m1"].inners["i1"].label.set("roundtrip"), ctx)
    assert run(Root.mids["m1"].inners["i1"].label, ctx)[0] == "roundtrip"


def test_write_two_siblings_shares_parent(ctx, data):
    run(Root.mids["m1"].inners["i1"].label.set("L"), ctx)
    run(Root.mids["m1"].inners["i1"].count.set(3), ctx)
    assert data["mids"]["m1"]["inners"]["i1"] == {"label": "L", "count": 3}


def test_leaf_overwrite(ctx):
    run(Root.mids["m1"].note.set("first"), ctx)
    run(Root.mids["m1"].note.set("second"), ctx)
    assert run(Root.mids["m1"].note, ctx)[0] == "second"


def test_leaf_erase(ctx, data):
    run(Root.mids["m1"].note.set("x"), ctx)
    run(Root.mids["m1"].note.erase(), ctx)
    assert "note" not in data["mids"]["m1"]


# --- shape-in-shape and list-index navigation ------------------------------


def test_shape_ref_navigation_roundtrip(ctx):
    run(Root.info.label.set("via-shape"), ctx)
    assert run(Root.info.label, ctx)[0] == "via-shape"


def test_list_index_navigation_roundtrip(ctx, data):
    data["rows"] = [{"label": "a"}, {"label": "b"}]
    assert run(Root.rows[1].label, ctx)[0] == "b"


# --- dynamic keys ----------------------------------------------------------


def test_dynamic_key_from_ref(ctx, data):
    # `active` yields "m1"; mids[active] must resolve to mids["m1"].
    data["active"] = "m1"
    data["mids"] = {"m1": {"note": "found"}}
    assert run(Root.mids[Root.active].note, ctx)[0] == "found"


def test_dynamic_key_reflects_updated_source(ctx, data):
    data["mids"] = {"m1": {"note": "one"}, "m2": {"note": "two"}}
    data["active"] = "m1"
    assert run(Root.mids[Root.active].note, ctx)[0] == "one"
    data["active"] = "m2"
    assert run(Root.mids[Root.active].note, ctx)[0] == "two"


def test_ref_as_key_is_a_read_effect(ctx):
    # The key ref sits in a value slot (children[1]) -> dual role fires -> READ.
    from nu.tree import reads

    term = Root.mids[Root.active].note
    read_types = {t.__name__ for t in {type(r) for r in reads(term)}}
    assert any("StrRef" in n for n in read_types)


# --- refs inside refs: dynamic key on a deep path --------------------------


def test_ref_key_on_deep_path(ctx, data):
    data["active"] = "m1"
    data["mids"] = {"m1": {"inners": {"i1": {"label": "nested-dyn"}}}}
    assert run(Root.mids[Root.active].inners["i1"].label, ctx)[0] == "nested-dyn"


def test_ref_key_deep_write_then_read(ctx, data):
    data["active"] = "mX"
    run(Root.mids[Root.active].inners["i1"].label.set("w"), ctx)
    assert data["mids"]["mX"]["inners"]["i1"]["label"] == "w"
    assert run(Root.mids[Root.active].inners["i1"].label, ctx)[0] == "w"


# --- inline_refs is retired: runtime resolution handles deep/dynamic chains -


def test_inline_refs_is_identity(ctx):
    import nu.mem as nu_mem

    chain = Root.mids["m1"].inners["i1"].label
    assert nu_mem.inline_refs(chain) is chain


# --- primitive dict/list navigation writes (D5: mem now provides _wrap_item_ref)


def test_primitive_dict_navigation_store_read_roundtrip(ctx, data):
    """Regression: mem DictRef navigation used to return a bare domain
    MutableItemRef with no substrate ``_write`` (crash on store). D5 routes
    ``[key]`` through ``_wrap_item_ref`` so mem builds its own item Ref."""
    from nu.mem import DictRef

    class Bag(Shape):
        d = DictRef.slot(str, str)

    bag_data: dict = {}
    bag_ctx = Context().bind(dict, bag_data, Bag)
    run(Bag.d["k"].set("v"), bag_ctx)
    assert bag_data == {"d": {"k": "v"}}
    assert run(Bag.d["k"], bag_ctx)[0] == "v"


def test_primitive_list_navigation_store_read_roundtrip():
    """Regression: same latent crash for mem ListRef element writes."""
    from nu.mem import ListRef

    class Bag(Shape):
        xs = ListRef.slot(int)

    bag_data = {"xs": [1, 2, 3]}
    bag_ctx = Context().bind(dict, bag_data, Bag)
    run(Bag.xs[0].set(9), bag_ctx)
    assert bag_data["xs"] == [9, 2, 3]
    assert run(Bag.xs[2], bag_ctx)[0] == 3
