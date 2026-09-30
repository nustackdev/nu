"""Dedicated functional tests for virtuals Ref *composition* — the hard cases.

Targets what the ref redesign is about, against a real virtuals transaction:
deep hierarchical navigation, write-path vivification, dynamic keys, and the
cross-fabric case that produced the `remaining-error.md` StrRef leak — a mem Ref
used as a dynamic key inside a virtuals chain. With the parent on the tree and
the path resolved at runtime, that key evaluates like any other child.
"""

from __future__ import annotations

from typing import ClassVar

from nu import Shape, run
from nu.lang import EMPTY
from nustd.kv import DictRef, IntRef, ListRef, ShapeRef, StrRef
from nustd.mem import StrRef as MemStrRef
from virtuals.views import DictView


# --- virtuals shapes: a 3-level hierarchy -----------------------------------


class Inner(Shape):
    label = StrRef.slot()
    count = IntRef.slot()


class Mid(Shape):
    inners = DictRef.slot(Inner)
    note = StrRef.slot()


class VRoot(Shape):
    mids = DictRef.slot(Mid)
    rows = ListRef.slot(Inner)
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
    assert run(VRoot.mids["m1"].note, ctx)[0] is EMPTY


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


# --- the value is positional, the key and view keyword-only -----------------


def test_dict_and_list_navigation_land_on_the_declared_leaf(ctx):
    """Regression: ``DictRef.slot(str, str)`` once meant key=str in mem and
    view=str in kv, and every kv write through that slot crashed. The key is
    keyword-only now, so one spelling means one thing in both fabrics."""
    from nustd.kv import DictRef, IntRef, ListRef, StrRef

    class V(Shape):
        d = DictRef.slot(str, key=str)
        rows = ListRef.slot(int)

    assert type(V.d["k"]) is StrRef
    assert type(V.rows[0]) is IntRef
    run(V.d["k"].set("v"), ctx)
    assert run(V.d["k"].upper(), ctx)[0] == "V"


# --- a custom view lays the container out on real reads and writes ----------


class ShoutingView(DictView):
    """A DictView that stores every string upper-cased and records each write.

    The upper-casing is visible in what storage hands back, and the record
    names the view class that took the write, so a slot that only recorded the
    view and still wrote through the default ``DictView`` would fail both.
    """

    writes: ClassVar[list[tuple[str, object]]] = []

    def __setitem__(self, address: str | int, value: object) -> None:
        type(self).writes.append((type(self).__name__, address))
        super().__setitem__(address, value.upper() if isinstance(value, str) else value)


class Viewed(Shape):
    loud = DictRef.slot(str, view=ShoutingView)
    plain = DictRef.slot(str)


def test_a_custom_view_is_the_one_reads_and_writes_go_through(ctx):
    ShoutingView.writes.clear()
    run(Viewed.loud["a"].set("gor"), ctx)
    run(Viewed.loud.set_item("b", "sam"), ctx)
    run(Viewed.plain["a"].set("gor"), ctx)

    assert type(run(Viewed.loud, ctx)[0]) is ShoutingView
    assert type(run(Viewed.plain, ctx)[0]) is DictView
    assert ShoutingView.writes == [("ShoutingView", "a"), ("ShoutingView", "b")]
    assert run(Viewed.loud["a"], ctx)[0] == "GOR"
    assert run(Viewed.loud.get_item("b"), ctx)[0] == "SAM"
    assert run(Viewed.plain["a"], ctx)[0] == "gor"
