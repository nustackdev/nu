"""Tests for Attribute and Schema."""

from __future__ import annotations

import pytest

from nu.engine import Attribute, CycleError, Schema, Symbol


class Kind(Symbol):
    sort = Attribute.declared("Kind")


def test_declared_constructor():
    a = Attribute.declared(42, name="answer")
    assert a.flavor == "declared"
    assert a.name == "answer"
    assert a.value == 42


def test_synthesized_constructor():
    base = lambda p, path: 0  # noqa: E731
    combine = lambda own, kids: own  # noqa: E731
    a = Attribute.synthesized("size", base, combine, reads=("sort",))
    assert a.flavor == "synthesized"
    assert a.base is base
    assert a.combine is combine
    assert a.reads == ("sort",)


def test_inherited_constructor():
    a = Attribute.inherited("depth", root=lambda p, path: 0, derive=lambda p, par, slot, up: up + 1)
    assert a.flavor == "inherited"
    assert a.root is not None
    assert a.derive is not None


def test_register_requires_a_name():
    schema = Schema()
    with pytest.raises(ValueError, match="must have a name"):
        schema.register(Attribute.declared(1))


def test_resolution_per_class_then_global():
    schema = Schema()
    schema.register(Attribute.declared("global", name="origin"))
    assert schema.attribute(Kind, "origin").value == "global"
    assert schema.attribute(Kind, "sort").value == "Kind"
    assert schema.attribute(Kind, "missing") is None


def test_per_class_overrides_global():
    schema = Schema()
    schema.register(Attribute.declared("default", name="sort"))
    # Kind declares its own `sort`, which wins.
    assert schema.attribute(Kind, "sort").value == "Kind"


def _noop_synth(name, reads):
    return Attribute.synthesized(name, lambda p, path: 0, lambda own, kids: own, reads=reads)


def test_finalize_topo_order_respects_reads():
    schema = Schema()
    schema.register(_noop_synth("c", reads=("b",)))
    schema.register(_noop_synth("b", reads=("a",)))
    schema.register(_noop_synth("a", reads=()))
    schema.finalize()
    order = schema.order()
    assert order.index("a") < order.index("b") < order.index("c")


def test_finalize_ignores_declared_dependencies():
    schema = Schema()
    schema.register(Attribute.declared(0, name="konst"))
    schema.register(_noop_synth("computed", reads=("konst",)))
    schema.finalize()
    assert schema.order() == ["computed"]


def test_finalize_detects_a_cycle():
    schema = Schema()
    schema.register(_noop_synth("x", reads=("y",)))
    schema.register(_noop_synth("y", reads=("x",)))
    with pytest.raises(CycleError):
        schema.finalize()


def test_order_before_finalize_raises():
    schema = Schema()
    with pytest.raises(RuntimeError, match="not finalized"):
        schema.order()


def test_register_invalidates_finalize():
    schema = Schema()
    schema.register(_noop_synth("a", reads=()))
    schema.finalize()
    schema.register(_noop_synth("b", reads=()))
    with pytest.raises(RuntimeError, match="not finalized"):
        schema.order()
