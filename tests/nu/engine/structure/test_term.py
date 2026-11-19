"""Unit tests for ``nu.engine.structure.term``.

Covers :class:`Term` -- its construction shape, ``evolve`` variants, fields,
the freeze after construction, ``__repr__``, the not-implemented
``eval``/``aeval`` defaults -- and :class:`TermMeta`'s attribute collection
across the MRO.
"""

from __future__ import annotations

import copy
import pickle
from typing import TypeVar

import pytest
from _support.terms import HeavyNode, Leaf, Node

import nu
from nu.engine import Runtime
from nu.engine.structure import Declared, FrozenTermError, Term
from nu.lang import wire


V = TypeVar("V")


# --- TermMeta: attribute collection ---------------------------------------


def test_metaclass_collects_a_classes_declared_attributes():
    assert set(Node._attributes) == {"sort", "weight"}
    assert Node._attributes["sort"].value == "Node"
    assert Node._attributes["weight"].value == 1


def test_metaclass_fills_in_a_missing_name_from_the_class_binding():
    assert Leaf._attributes["sort"].name == "sort"


def test_subclass_inherits_parent_attributes():
    # ``HeavyNode`` declares only ``weight`` but inherits ``sort`` from ``Node``.
    assert set(HeavyNode._attributes) == {"sort", "weight"}


def test_subclass_override_wins_over_parent():
    assert HeavyNode._attributes["weight"].value == 9
    assert HeavyNode._attributes["sort"].value == "Node"


def test_base_term_has_no_attributes():
    assert Term._attributes == {}


def test_a_declared_attribute_with_an_explicit_name_keeps_it():
    class Custom(Term):
        anything = Declared(value=1, name="aliased")

    assert "aliased" in Custom._attributes
    assert "anything" not in Custom._attributes


# --- Term: construction ---------------------------------------------------


def test_children_is_a_tuple_of_terms():
    a, b = Leaf(), Leaf()
    parent = Node(a, b)
    assert nu.tree.children(parent) == (a, b)
    assert isinstance(nu.tree.children(parent), tuple)


def test_a_leaf_has_no_children():
    assert nu.tree.children(Leaf()) == ()


def test_a_bare_term_holds_its_children_and_no_fields():
    assert vars(Leaf()) == {"_children": (), "_frozen": True}
    assert nu.tree.fields(Leaf()) == {}


# --- Term: evolve ---------------------------------------------------------


def test_evolve_returns_a_new_term_of_the_same_kind():
    original = Node(Leaf(), Leaf())
    variant = original.evolve(children=(Leaf(),))
    assert type(variant) is Node
    assert variant is not original


def test_evolve_replaces_the_children_tuple():
    a, b, c = Leaf(), Leaf(), Leaf()
    original = Node(a, b)
    variant = original.evolve(children=(c,))
    assert nu.tree.children(variant) == (c,)
    assert nu.tree.children(original) == (a, b)


def test_evolve_shares_field_values_by_reference():
    held = {"k": "v"}
    original = nu.Literal(held)
    variant = original.evolve(children=())
    assert variant is not original
    assert variant.value is held


class Boxed(Term):
    def __init__(self, *children: Term, size: int = 0, tag: str = "") -> None:
        super().__init__(*children)
        self.size = size
        self.tag = tag


def test_evolve_without_arguments_is_an_equal_copy():
    original = Boxed(Leaf(), size=3)
    variant = original.evolve()
    assert variant is not original
    assert nu.tree.equal(variant, original)


def test_evolve_overrides_fields_and_keeps_the_rest():
    original = Boxed(Leaf(), size=3, tag="a")
    variant = original.evolve(size=4)
    assert nu.tree.fields(variant) == {"size": 4, "tag": "a"}
    assert nu.tree.fields(original) == {"size": 3, "tag": "a"}
    assert nu.tree.children(variant) == nu.tree.children(original)


def test_evolve_takes_children_and_fields_together():
    a, b = Leaf(), Leaf()
    variant = Boxed(a, size=1).evolve(children=[b], tag="z")
    assert nu.tree.children(variant) == (b,)
    assert nu.tree.fields(variant) == {"size": 1, "tag": "z"}


def test_equal_tells_fields_apart():
    assert nu.tree.equal(Boxed(size=1), Boxed(size=1))
    assert not nu.tree.equal(Boxed(size=1), Boxed(size=2))


def test_a_term_with_fields_pickles_round_trip():
    original = Boxed(Leaf(), size=5, tag="t")
    for back in (pickle.loads(pickle.dumps(original)), wire.loads(wire.dumps(original))):  # noqa: S301 -- own bytes
        assert nu.tree.equal(back, original)


# --- Term: frozen after construction -------------------------------------


class Sized(Boxed):
    """A subclass whose ``__init__`` runs the base's, then writes over it."""

    def __init__(self, *children: Term, size: int = 0) -> None:
        super().__init__(*children, size=size, tag="sized")
        self.size = size * 2
        self._children = (*self._children, Leaf())


def test_setting_a_field_after_construction_raises():
    term = Boxed(size=1)
    with pytest.raises(FrozenTermError, match="evolve"):
        term.size = 2
    with pytest.raises(FrozenTermError):
        term.new_field = 1
    assert nu.tree.fields(term) == {"size": 1, "tag": ""}


def test_replacing_children_after_construction_raises():
    term = Node(Leaf())
    with pytest.raises(FrozenTermError):
        term._children = ()


def test_deleting_a_field_after_construction_raises():
    term = Boxed(size=1)
    with pytest.raises(FrozenTermError):
        del term.size
    assert term.size == 1


def test_frozen_term_error_is_an_attribute_error():
    assert issubclass(FrozenTermError, AttributeError)


def test_a_subclass_init_writes_freely_until_the_outermost_init_returns():
    term = Sized(Leaf(), size=3)
    assert nu.tree.fields(term) == {"size": 6, "tag": "sized"}
    assert len(nu.tree.children(term)) == 2
    with pytest.raises(FrozenTermError):
        term.size = 1


def test_a_generic_term_constructs_through_its_alias():
    # typing sets ``__orig_class__`` after construction and swallows the
    # AttributeError, so the alias neither fails nor leaks a field.
    class Typed(Term[Runtime, V]):
        pass

    term = Typed[int](Leaf())
    assert len(nu.tree.children(term)) == 1
    assert nu.tree.fields(term) == {}
    with pytest.raises(FrozenTermError):
        term.size = 1


def test_evolve_builds_a_frozen_variant_and_leaves_the_original():
    original = Boxed(Leaf(), size=3, tag="a")
    variant = original.evolve(children=(), size=4)
    assert nu.tree.fields(original) == {"size": 3, "tag": "a"}
    assert len(nu.tree.children(original)) == 1
    with pytest.raises(FrozenTermError):
        variant.size = 5
    assert variant.size == 4


def _local_boxed() -> Term:
    class Local(Term):
        def __init__(self, size: int) -> None:
            super().__init__()
            self.size = size

    return Local(7)


@pytest.mark.parametrize(
    "round_trip",
    [
        copy.copy,
        copy.deepcopy,
        lambda t: pickle.loads(pickle.dumps(t)),  # noqa: S301 -- own bytes
        lambda t: wire.loads(wire.dumps(t)),
    ],
    ids=["copy", "deepcopy", "pickle", "cloudpickle"],
)
def test_copies_and_unpickled_terms_stay_frozen(round_trip):
    back = round_trip(Boxed(Leaf(), size=5, tag="t"))
    assert back.size == 5
    with pytest.raises(FrozenTermError):
        back.size = 6


def test_a_term_of_a_local_class_crosses_the_wire_frozen():
    back = wire.loads(wire.dumps(_local_boxed()))
    assert back.size == 7
    with pytest.raises(FrozenTermError):
        back.size = 8


def test_a_bare_instance_never_constructed_is_not_frozen():
    bare = Boxed.__new__(Boxed)
    bare._children = ()
    assert nu.tree.children(bare) == ()


# --- Term: repr -----------------------------------------------------------


def test_repr_of_a_childless_term_is_its_class_name():
    assert repr(Leaf()) == "Leaf"


def test_repr_nests_children_inside_parens():
    assert repr(Node(Leaf(), Leaf())) == "Node(Leaf, Leaf)"


# --- Term: eval / aeval fallbacks -----------------------------------------


def test_eval_raises_not_implemented_by_default():
    with pytest.raises(NotImplementedError, match=r"Leaf\._eval"):
        Leaf()._eval(rt=None, nid=0)


async def test_aeval_raises_not_implemented_by_default():
    with pytest.raises(NotImplementedError, match=r"Leaf\._aeval"):
        await Leaf()._aeval(rt=None, nid=0)


def test_default_compile_thunk_defers_to_eval():
    # The default ``_compile`` builds a thunk that, when called, invokes
    # ``_eval`` -- which itself raises. Construction is total; the failure
    # surfaces at thunk call time, not at compile time.
    thunk = Leaf()._compile(nid=0, children=())
    with pytest.raises(NotImplementedError):
        thunk(None)


async def test_default_acompile_thunk_defers_to_aeval():
    athunk = Leaf()._acompile(nid=0, children=())
    with pytest.raises(NotImplementedError):
        await athunk(None)
