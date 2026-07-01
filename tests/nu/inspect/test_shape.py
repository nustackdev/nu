"""Tests for nu.inspect.render_shape - the Shape + storage tree renderer.

Renders a Shape class against plain-dict storage (the substrate-free path):
walks ``Shape._slots``, classifies each slot by its Ref class, and prints the
backing data as a tree. The ANSI form only adds color, so we assert on plain.
"""

from __future__ import annotations

from nu.domains.shape import Shape, Slot
from nu.domains.shape.refs.item import ItemRef
from nu.domains.shape.refs.mapping import MappingRef
from nu.domains.shape.refs.sequence import SequenceRef
from nu.domains.shape.refs.shape import ShapeRef
from nu.inspect import render_shape


class Inner(Shape):
    x = Slot(ItemRef)
    y = Slot(ItemRef)


class Order(Shape):
    price = Slot(ItemRef)
    tags = Slot(SequenceRef)
    meta = Slot(MappingRef)
    inner = Slot(ShapeRef, shape_type=Inner)


def test_header_is_the_shape_name() -> None:
    out = render_shape(Order, {}, as_="plain")
    assert out.splitlines()[0] == "Order"


def test_scalar_slot_renders_value() -> None:
    out = render_shape(Order, {"price": 42.5}, as_="plain")
    assert "price" in out
    assert "42.5" in out


def test_list_and_dict_slots() -> None:
    out = render_shape(Order, {"tags": ["a", "b"], "meta": {"k": 1}}, as_="plain")
    assert "['a', 'b']" in out
    assert "{'k': 1}" in out


def test_nested_shape_expands() -> None:
    out = render_shape(Order, {"inner": {"x": 1, "y": 2}}, as_="plain")
    lines = out.splitlines()
    assert any(line.strip().endswith("Inner") for line in lines)
    # the nested slots render under the Inner header
    assert any("x" in line for line in lines)
    assert any("y" in line for line in lines)


def test_missing_storage_renders_empty_markers() -> None:
    out = render_shape(Order, None, as_="plain")
    assert out.splitlines()[0] == "Order"  # still renders the schema
    assert "price" in out


def test_ansi_form_carries_escapes() -> None:
    ansi = render_shape(Order, {"price": 1}, as_="ansi")
    plain = render_shape(Order, {"price": 1}, as_="plain")
    assert "\033[" in ansi
    assert "\033[" not in plain
