"""Tests for nu.lang.render - the two renderings every Nu term shows itself as.

``render_str`` is the box-tree behind ``__str__``, in two forms: ``"plain"``
(no escapes) and ``"ansi"`` (color). The plain form is what we assert structure
on; the ansi form we only check carries escapes and the same node labels.
``render_repr`` is the one-line constructor form behind ``__repr__``.
"""

from __future__ import annotations

from nu.core import Add, Mul, Print
from nu.core.flows import Sequential
from nu.core.io import STDIN, STDOUT, Input
from nu.lang import Literal, Nu
from nu.lang.render import render_repr, render_str


def test_single_node() -> None:
    out = render_str(Literal(42), as_="plain")
    assert out == "Literal(42)"


def test_nested_tree_shape() -> None:
    out = render_str(Add(Mul(2, 3), Literal(4)), as_="plain")
    lines = out.splitlines()
    assert lines[0] == "● Add"  # non-Literal Query is dotted
    assert lines[1] == "├── ● Mul"
    assert lines[2] == "│  ├── Literal(2)"
    assert lines[3] == "│  └── Literal(3)"
    assert lines[4] == "└── Literal(4)"


def test_literal_dot_only_for_non_literal_query() -> None:
    # A Literal is a Query but must NOT get the value-producer dot.
    out = render_str(Literal("x"), as_="plain")
    assert not out.startswith("●")


def test_ref_label_shows_payload() -> None:
    out = render_str(STDOUT, as_="plain")
    assert out == "StdioRef(stream='stdout')"


def test_ref_label_shows_owner_shape() -> None:
    # A structured (Shape) Ref shows its owning Shape, not a payload hint.
    from nu.domains.shape import Shape, Slot
    from nu.domains.shape.refs.item import ItemRef

    class Widget(Shape):
        size = Slot(ItemRef)

    ref = ItemRef("size", owner_shape=Widget)
    label = render_str(ref, as_="plain").splitlines()[0]
    assert label.startswith("ItemRef[Widget]")


def test_effectful_program() -> None:
    program = Sequential(
        Print(STDOUT, Literal("hi")),
        Input(STDIN),
    )
    lines = render_str(program, as_="plain").splitlines()
    assert lines[0] == "Sequential"
    assert "Print" in lines[1]
    assert "StdioRef(stream='stdout')" in lines[2]
    assert "Input" in lines[-2]
    assert "StdioRef(stream='stdin')" in lines[-1]


def test_ansi_has_escapes_and_labels() -> None:
    tree = Add(1, 2)
    ansi = render_str(tree, as_="ansi")
    plain = render_str(tree, as_="plain")
    assert "\033[" in ansi  # carries color
    assert "\033[" not in plain  # plain does not
    # both name the same nodes
    assert "Add" in ansi
    assert "Literal(1)" in ansi


def test_custom_label_callable() -> None:
    out = render_str(
        Add(1, 2),
        as_="plain",
        label=lambda n: type(n).__name__.upper(),
    )
    lines = out.splitlines()
    assert lines[0] == "ADD"
    assert lines[1] == "├── LITERAL"
    assert lines[2] == "└── LITERAL"


# --- render_repr, and the single-source-of-truth invariant -------------------


def test_repr_is_the_one_line_constructor_form() -> None:
    assert render_repr(Add(1, 2)) == "Add(1, 2)"
    assert render_repr(Sequential(Add(1, 2), Print("x"))) == "Sequential(Add(1, 2), Print('x'))"


def test_repr_unwraps_a_literal_to_its_bare_value() -> None:
    assert render_repr(Literal(42)) == "42"
    assert render_repr(Literal("hi")) == "'hi'"


def test_repr_surfaces_payload_on_a_childless_term() -> None:
    # A childless atom keeps everything it is in the payload; without it the
    # stdio singletons would repr as a bare class name.
    assert render_repr(STDOUT) == "StdioRef(stream='stdout')"


def test_the_dunders_route_through_this_module() -> None:
    tree = Add(1, 2)
    assert repr(tree) == render_repr(tree)
    assert str(tree) == render_str(tree, as_="plain")


def test_no_nu_subclass_overrides_the_display_dunders() -> None:
    """Display lives in nu.lang.render and nowhere else.

    A per-class ``__repr__`` / ``__str__`` silently wins over the language's
    rendering, so a term would show itself differently depending on which atom
    it is. Import the fabrics, walk every Nu subclass, and assert none of them
    define one.
    """
    import importlib

    for mod in (
        "nu.core",
        "nu.context",
        "nu.domains.shape",
        "nu.domains.service",
        "nu.prog",
        "nu.std",
        "nu.mem",
        "nu.kv",
        "nu.proxy",
        "nu.mp",
    ):
        importlib.import_module(mod)

    seen: set[type] = set()

    def walk(cls: type) -> None:
        for sub in cls.__subclasses__():
            if sub in seen:
                continue
            seen.add(sub)
            walk(sub)

    walk(Nu)
    assert seen, "expected the Nu hierarchy to be populated"
    offenders = [
        f"{c.__module__}.{c.__name__}"
        for c in seen
        if any(name in c.__dict__ for name in ("__repr__", "__str__", "__format__"))
    ]
    assert offenders == []
