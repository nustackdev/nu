"""Unit tests for ``nu.engine.structure.attribute``.

Covers the :class:`Attribute` hierarchy: the three concrete kinds
(:class:`Declared`, :class:`Synthesized`, :class:`Inherited`), the abstract
:class:`Computed` middle base, and the dataclass shape (kw-only fields,
defaults, equality, repr).
"""

from __future__ import annotations

import pytest

from nu.engine.structure import (
    Attribute,
    Computed,
    Declared,
    Inherited,
    Synthesized,
)


# --- construction shape ----------------------------------------------------


def test_declared_carries_a_value():
    a = Declared(value=42)
    assert a.value == 42
    assert a.name is None


def test_declared_takes_an_explicit_name():
    a = Declared(value=42, name="answer")
    assert a.name == "answer"
    assert a.value == 42


def test_synthesized_carries_base_combine_and_reads():
    def base(p, path):
        return 0

    def combine(own, children):
        return own

    a = Synthesized(name="size", base=base, combine=combine, reads=("sort",))
    assert a.name == "size"
    assert a.base is base
    assert a.combine is combine
    assert a.reads == ("sort",)


def test_synthesized_reads_default_to_empty():
    a = Synthesized(name="x", base=lambda p, path: 0, combine=lambda o, c: o)
    assert a.reads == ()


def test_inherited_carries_root_derive_and_reads():
    def root(p, path):
        return 0

    def derive(p, par, slot, up):
        return up + 1

    a = Inherited(name="depth", root=root, derive=derive, reads=("sort",))
    assert a.root is root
    assert a.derive is derive
    assert a.reads == ("sort",)


def test_inherited_reads_default_to_empty():
    a = Inherited(name="d", root=lambda p, path: 0, derive=lambda p, par, slot, up: up)
    assert a.reads == ()


def test_attribute_construction_is_keyword_only():
    # Passing required fields positionally must fail; all subclasses use
    # ``kw_only=True`` on the underlying dataclass.
    with pytest.raises(TypeError):
        Declared(42)  # type: ignore[misc]
    with pytest.raises(TypeError):
        Synthesized("x", lambda p, path: 0, lambda o, c: o)  # type: ignore[misc]


# --- hierarchy and isinstance ----------------------------------------------


@pytest.mark.parametrize("kind", [Declared, Synthesized, Inherited])
def test_concrete_kinds_subclass_attribute(kind):
    assert issubclass(kind, Attribute)


@pytest.mark.parametrize("kind", [Synthesized, Inherited])
def test_computed_kinds_subclass_computed(kind):
    assert issubclass(kind, Computed)


def test_declared_is_not_a_computed_attribute():
    a = Declared(value=1)
    assert not isinstance(a, Computed)


def test_isinstance_replaces_a_flavor_check():
    # The dispatch from the old ``flavor`` string discriminator is now
    # the type itself; downstream code uses ``isinstance``.
    attrs: list[Attribute] = [
        Declared(value=0),
        Synthesized(name="a", base=lambda p, path: 0, combine=lambda o, c: o),
        Inherited(name="b", root=lambda p, path: 0, derive=lambda p, par, slot, up: up),
    ]
    assert sum(isinstance(a, Declared) for a in attrs) == 1
    assert sum(isinstance(a, Computed) for a in attrs) == 2
    assert sum(isinstance(a, Synthesized) for a in attrs) == 1
    assert sum(isinstance(a, Inherited) for a in attrs) == 1


# --- dataclass shape -------------------------------------------------------


def test_declared_equality_is_structural():
    assert Declared(value=1, name="x") == Declared(value=1, name="x")
    assert Declared(value=1, name="x") != Declared(value=2, name="x")
    assert Declared(value=1, name="x") != Declared(value=1, name="y")


def test_repr_includes_kind_and_name():
    assert repr(Declared(value=1, name="x")) == "Declared('x')"
    assert (
        repr(
            Synthesized(
                name="y",
                base=lambda p, path: 0,
                combine=lambda o, c: o,
            )
        )
        == "Synthesized('y')"
    )
    assert (
        repr(
            Inherited(
                name="z",
                root=lambda p, path: 0,
                derive=lambda p, par, slot, up: up,
            )
        )
        == "Inherited('z')"
    )
