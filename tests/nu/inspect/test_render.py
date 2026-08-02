"""Tests for nu.inspect.render_nu - the Nu-tree box-tree renderer.

Two forms: ``"plain"`` (no escapes) and ``"ansi"`` (color). The plain form is
what we assert structure on; the ansi form we only check carries escapes and
the same node labels.
"""

from __future__ import annotations

from nu.core import Add, Literal, Mul, Print
from nu.core.io import STDIN, STDOUT, Input
from nu.flows import Sequential
from nu.inspect import render_nu


def test_single_node() -> None:
    out = render_nu(Literal(42), as_="plain")
    assert out == "Literal(42)"


def test_nested_tree_shape() -> None:
    out = render_nu(Add(Mul(2, 3), Literal(4)), as_="plain")
    lines = out.splitlines()
    assert lines[0] == "● Add"  # non-Literal Query is dotted
    assert lines[1] == "├── ● Mul"
    assert lines[2] == "│  ├── Literal(2)"
    assert lines[3] == "│  └── Literal(3)"
    assert lines[4] == "└── Literal(4)"


def test_literal_dot_only_for_non_literal_query() -> None:
    # A Literal is a Query but must NOT get the value-producer dot.
    out = render_nu(Literal("x"), as_="plain")
    assert not out.startswith("●")


def test_ref_label_shows_payload() -> None:
    out = render_nu(STDOUT, as_="plain")
    assert out == "StdioRef(stream='stdout')"


def test_ref_label_shows_owner_shape() -> None:
    # A structured (Shape) Ref shows its owning Shape, not a payload hint.
    from nu.domains.shape import Shape, Slot
    from nu.domains.shape.refs.item import ItemRef

    class Widget(Shape):
        size = Slot(ItemRef)

    ref = ItemRef("size", owner_shape=Widget)
    label = render_nu(ref, as_="plain").splitlines()[0]
    assert label.startswith("ItemRef[Widget]")


def test_effectful_program() -> None:
    program = Sequential(
        Print(STDOUT, Literal("hi")),
        Input(STDIN),
    )
    lines = render_nu(program, as_="plain").splitlines()
    assert lines[0] == "Sequential"
    assert "Print" in lines[1]
    assert "StdioRef(stream='stdout')" in lines[2]
    assert "Input" in lines[-2]
    assert "StdioRef(stream='stdin')" in lines[-1]


def test_ansi_has_escapes_and_labels() -> None:
    tree = Add(1, 2)
    ansi = render_nu(tree, as_="ansi")
    plain = render_nu(tree, as_="plain")
    assert "\033[" in ansi  # carries color
    assert "\033[" not in plain  # plain does not
    # both name the same nodes
    assert "Add" in ansi
    assert "Literal(1)" in ansi


def test_custom_label_callable() -> None:
    out = render_nu(
        Add(1, 2),
        as_="plain",
        label=lambda n: type(n).__name__.upper(),
    )
    lines = out.splitlines()
    assert lines[0] == "ADD"
    assert lines[1] == "├── LITERAL"
    assert lines[2] == "└── LITERAL"
