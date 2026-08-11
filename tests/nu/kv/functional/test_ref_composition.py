"""Dedicated functional tests for virtuals Ref *composition* — the hard cases.

Targets what the ref redesign is about, against a real virtuals transaction:
deep hierarchical navigation, write-path vivification, dynamic keys, and the
cross-fabric case that produced the `remaining-error.md` StrRef leak — a mem Ref
used as a dynamic key inside a virtuals chain. With the parent on the tree and
the path resolved at runtime, that key evaluates like any other child.
"""

from __future__ import annotations

from nu import Shape, run
from nu.kv import IntRef, ShapeRef, ShapesDictRef, ShapesListRef, StrRef
from nu.lang import EMPTY
from nu.mem import StrRef as MemStrRef


# --- virtuals shapes: a 3-level hierarchy -----------------------------------


class Inner(Shape):
    label = StrRef.slot()
    count = IntRef.slot()


class Mid(Shape):
    inners = ShapesDictRef.slot(Inner)
    note = StrRef.slot()


class VRoot(Shape):
    mids = ShapesDictRef.slot(Mid)
    rows = ShapesListRef.slot(Inner)
    info = ShapeRef.slot(Inner)
    active = StrRef.slot()  # a virtuals key source


# --- mem shape for the cross-fabric key -------------------------------------


class MemBag(Shape):
    current = MemStrRef.slot()


def _rt(ref, value, ctx):
    run(ref.set(value), ctx)
    return run(ref, ctx)[0]


# --- deep navigation + vivification -----------------------------------------


def test_three_deep_write_then_read(ctx):
    run(VRoot.mids["m1"].inners["i1"].label.set("deep"), ctx)
    assert run(VRoot.mids["m1"].inners["i1"].label, ctx)[0] == "deep"


def test_three_deep_vivifies_intermediate(ctx):
    # Writing a leaf under empty storage must create the whole chain.
    run(VRoot.mids["m1"].inners["i1"].count.set(42), ctx)
    assert run(VRoot.mids["m1"].inners["i1"].count, ctx)[0] == 42


def test_sibling_leaves_share_parent(ctx):
    run(VRoot.mids["m1"].inners["i1"].label.set("L"), ctx)
    run(VRoot.mids["m1"].inners["i1"].count.set(3), ctx)
    assert run(VRoot.mids["m1"].inners["i1"].label, ctx)[0] == "L"
    assert run(VRoot.mids["m1"].inners["i1"].count, ctx)[0] == 3


def test_leaf_overwrite(ctx):
    run(VRoot.mids["m1"].note.set("first"), ctx)
    run(VRoot.mids["m1"].note.set("second"), ctx)
    assert run(VRoot.mids["m1"].note, ctx)[0] == "second"


def test_leaf_erase(ctx):
    run(VRoot.mids["m1"].note.set("x"), ctx)
    run(VRoot.mids["m1"].note.erase(), ctx)
    assert run(VRoot.mids["m1"].note, ctx)[0] == EMPTY


# --- shape-ref navigation ---------------------------------------------------


def test_shape_ref_navigation_roundtrip(ctx):
    assert _rt(VRoot.info.label, "via-shape", ctx) == "via-shape"


# --- dynamic keys (same fabric) ---------------------------------------------


def test_dynamic_key_from_virtuals_ref(ctx):
    run(VRoot.active.set("m1"), ctx)
    run(VRoot.mids["m1"].note.set("found"), ctx)
    assert run(VRoot.mids[VRoot.active].note, ctx)[0] == "found"


def test_dynamic_key_reflects_updated_source(ctx):
    run(VRoot.mids["m1"].note.set("one"), ctx)
    run(VRoot.mids["m2"].note.set("two"), ctx)
    run(VRoot.active.set("m1"), ctx)
    assert run(VRoot.mids[VRoot.active].note, ctx)[0] == "one"
    run(VRoot.active.set("m2"), ctx)
    assert run(VRoot.mids[VRoot.active].note, ctx)[0] == "two"


def test_dynamic_key_on_deep_path(ctx):
    run(VRoot.active.set("m1"), ctx)
    run(VRoot.mids["m1"].inners["i1"].label.set("nested-dyn"), ctx)
    assert run(VRoot.mids[VRoot.active].inners["i1"].label, ctx)[0] == "nested-dyn"


# --- cross-fabric: a mem Ref used as a virtuals key (remaining-error.md repro)


def test_cross_fabric_mem_ref_as_virtuals_key(ctx):
    mem_data = {"current": "mint1"}
    xctx = ctx.bind(dict, mem_data, MemBag)
    run(VRoot.mids["mint1"].note.set("creatorX"), xctx)
    # The key `MemBag.current` is a *mem* ref inside a *virtuals* chain.
    assert run(VRoot.mids[MemBag.current].note, xctx)[0] == "creatorX"


def test_cross_fabric_mem_key_on_deep_path(ctx):
    mem_data = {"current": "mint1"}
    xctx = ctx.bind(dict, mem_data, MemBag)
    run(VRoot.mids["mint1"].inners["i1"].label.set("cc"), xctx)
    assert run(VRoot.mids[MemBag.current].inners["i1"].label, xctx)[0] == "cc"


def test_cross_fabric_mem_key_write_then_read(ctx):
    mem_data = {"current": "mintZ"}
    xctx = ctx.bind(dict, mem_data, MemBag)
    run(VRoot.mids[MemBag.current].note.set("written"), xctx)
    assert run(VRoot.mids["mintZ"].note, xctx)[0] == "written"


# --- primitive collection navigation reads value_type off payload -----------


def test_primitive_dict_and_list_navigation_reads_payload():
    """Regression: virtuals DictRef/ListRef.__getitem__ builds the child ItemRef
    from ``value_type`` in ``payload`` (the payload migration privatized the old
    public ``value_type``/``item_type`` attrs, so a stale ``self.value_type``
    read would AttributeError here)."""
    from nu.kv import DictRef, ListRef

    class V(Shape):
        d = DictRef.slot(str, str)
        rows = ListRef.slot(int)

    di = V.d["k"]
    li = V.rows[0]
    assert di._payload["type_marker"] is str
    assert li._payload["type_marker"] is int
