"""Tests for Symbol and SymbolMeta."""

from __future__ import annotations

from nu2.engine import Attribute, Symbol


class Leaf(Symbol):
    sort = Attribute.declared("Leaf")


class Node(Symbol):
    sort = Attribute.declared("Node")
    weight = Attribute.declared(1)


class HeavyNode(Node):
    weight = Attribute.declared(9)


def test_metaclass_collects_attributes_with_names():
    assert set(Node._attributes) == {"sort", "weight"}
    assert Node._attributes["sort"].name == "sort"
    assert Node._attributes["sort"].value == "Node"


def test_subclass_inherits_and_overrides():
    assert set(HeavyNode._attributes) == {"sort", "weight"}
    assert HeavyNode._attributes["weight"].value == 9
    assert HeavyNode._attributes["sort"].value == "Node"


def test_base_symbol_has_no_attributes():
    assert Symbol._attributes == {}


def test_children_is_a_tuple():
    a, b = Leaf(), Leaf()
    parent = Node(a, b)
    assert parent.children == (a, b)
    assert isinstance(parent.children, tuple)


def test_payload_defaults_empty():
    assert Leaf().payload == {}


def test_with_children_makes_a_variant():
    a, b, c = Leaf(), Leaf(), Leaf()
    original = Node(a, b)
    variant = original.with_children(c)
    assert variant.children == (c,)
    assert original.children == (a, b)
    assert type(variant) is Node
    assert variant is not original


def test_with_children_shares_payload():
    original = Node()
    original.payload["k"] = "v"
    variant = original.with_children(Leaf())
    assert variant.payload == {"k": "v"}


def test_repr():
    assert repr(Leaf()) == "Leaf"
    assert repr(Node(Leaf(), Leaf())) == "Node(Leaf, Leaf)"
