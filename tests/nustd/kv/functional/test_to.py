"""``.to`` on kv item refs: name the kind at the address, keep going in it."""

from __future__ import annotations

from nu import Shape, run
from nu.domains.shape import ItemRef as CoreItemRef
from nustd.kv import DictRef, IntRef, ObjectRef, ShapeRef, StrRef
from nustd.kv.refs.items import ItemRef


class Order(Shape):
    qty = IntRef.slot()
    tags = DictRef.slot(str)


class Store(Shape):
    things = DictRef.slot(object)
    orders = DictRef.slot(Order)


def test_kv_leaves_are_core_item_refs():
    assert issubclass(ItemRef, CoreItemRef)
    assert isinstance(Store.things["a"], ObjectRef)


def test_to_a_leaf_class(ctx):
    n = Store.things["n"].to(IntRef)
    assert type(n) is IntRef
    run(n.set(4) >> n.inc(), ctx)
    assert run(Store.things.get_item("n"), ctx)[0] == 5


def test_to_a_container_spec(ctx):
    d = Store.things["d"].to(DictRef.slot(int))
    assert type(d["k"]) is IntRef
    run(d["k"].set(1), ctx)
    assert run(Store.things["d"].to(DictRef.slot(int)).get_item("k"), ctx)[0] == 1


def test_to_a_shape_spec(ctx):
    order = Store.things["o"].to(ShapeRef.slot(Order))
    run(order.qty.set(2) >> order.tags["a"].set("x"), ctx)
    again = Store.things["o"].to(ShapeRef.slot(Order))
    assert run(again.qty, ctx)[0] == 2
    assert run(again.tags["a"], ctx)[0] == "x"


def test_to_chains_several_levels(ctx):
    leaf = (
        Store.things["a"]
        .to(DictRef.slot(object))["b"]
        .to(ShapeRef.slot(Order))
        .tags["t"]
        .to(StrRef)
    )
    run(leaf.set("deep"), ctx)
    back = Store.things["a"].to(DictRef.slot(object))["b"].to(ShapeRef.slot(Order)).tags["t"]
    assert run(back, ctx)[0] == "deep"


def test_to_under_a_declared_container(ctx):
    run(Store.orders["x"].tags["t"].to(StrRef).set("y"), ctx)
    assert run(Store.orders["x"].tags["t"], ctx)[0] == "y"
