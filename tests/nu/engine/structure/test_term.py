"""Unit tests for ``nu.engine.structure.term``.

Covers :class:`Term` -- its construction shape, ``with_children`` variant,
``payload``, ``__repr__``, the not-implemented ``eval``/``aeval`` defaults --
and :class:`TermMeta`'s attribute collection across the MRO.
"""

from __future__ import annotations

import pytest
from _support.terms import HeavyNode, Leaf, Node

from nu.engine.structure import Declared, Term


# --- TermMeta: attribute collection ---------------------------------------


def test_metaclass_collects_a_classes_declared_attributes():
    assert set(Node.attributes) == {"sort", "weight"}
    assert Node.attributes["sort"].value == "Node"
    assert Node.attributes["weight"].value == 1


def test_metaclass_fills_in_a_missing_name_from_the_class_binding():
    assert Leaf.attributes["sort"].name == "sort"


def test_subclass_inherits_parent_attributes():
    # ``HeavyNode`` declares only ``weight`` but inherits ``sort`` from ``Node``.
    assert set(HeavyNode.attributes) == {"sort", "weight"}


def test_subclass_override_wins_over_parent():
    assert HeavyNode.attributes["weight"].value == 9
    assert HeavyNode.attributes["sort"].value == "Node"


def test_base_term_has_no_attributes():
    assert Term.attributes == {}


def test_a_declared_attribute_with_an_explicit_name_keeps_it():
    class Custom(Term):
        anything = Declared(value=1, name="aliased")

    assert "aliased" in Custom.attributes
    assert "anything" not in Custom.attributes


# --- Term: construction ---------------------------------------------------


def test_children_is_a_tuple_of_terms():
    a, b = Leaf(), Leaf()
    parent = Node(a, b)
    assert parent.children == (a, b)
    assert isinstance(parent.children, tuple)


def test_a_leaf_has_no_children():
    assert Leaf().children == ()


def test_payload_defaults_to_an_empty_dict():
    assert Leaf().payload == {}


def test_each_instance_gets_its_own_payload():
    a, b = Leaf(), Leaf()
    a.payload["k"] = "v"
    assert b.payload == {}


# --- Term: with_children --------------------------------------------------


def test_with_children_returns_a_new_term_of_the_same_kind():
    original = Node(Leaf(), Leaf())
    variant = original.with_children(Leaf())
    assert type(variant) is Node
    assert variant is not original


def test_with_children_replaces_the_children_tuple():
    a, b, c = Leaf(), Leaf(), Leaf()
    original = Node(a, b)
    variant = original.with_children(c)
    assert variant.children == (c,)
    assert original.children == (a, b)


def test_with_children_shares_the_payload_object():
    original = Node()
    original.payload["k"] = "v"
    variant = original.with_children(Leaf())
    assert variant.payload is original.payload


# --- Term: repr -----------------------------------------------------------


def test_repr_of_a_childless_term_is_its_class_name():
    assert repr(Leaf()) == "Leaf"


def test_repr_nests_children_inside_parens():
    assert repr(Node(Leaf(), Leaf())) == "Node(Leaf, Leaf)"


def test_repr_prefers_a_payload_name():
    term = Leaf()
    term.payload["name"] = "foo"
    assert repr(term) == "foo"


def test_repr_prefers_a_payload_value():
    term = Leaf()
    term.payload["value"] = 42
    assert repr(term) == "42"


# --- Term: eval / aeval fallbacks -----------------------------------------


def test_eval_raises_not_implemented_by_default():
    with pytest.raises(NotImplementedError, match=r"Leaf\.eval"):
        Leaf().eval(rt=None, nid=0)


async def test_aeval_raises_not_implemented_by_default():
    with pytest.raises(NotImplementedError, match=r"Leaf\.aeval"):
        await Leaf().aeval(rt=None, nid=0)


def test_default_compile_thunk_defers_to_eval():
    # The default ``compile`` builds a thunk that, when called, invokes
    # ``eval`` -- which itself raises. Construction is total; the failure
    # surfaces at thunk call time, not at compile time.
    thunk = Leaf().compile(nid=0, children=())
    with pytest.raises(NotImplementedError):
        thunk(None)


async def test_default_acompile_thunk_defers_to_aeval():
    athunk = Leaf().acompile(nid=0, children=())
    with pytest.raises(NotImplementedError):
        await athunk(None)
