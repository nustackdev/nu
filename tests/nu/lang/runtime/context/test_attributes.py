"""Unit tests for ``nu.lang.runtime.context.attributes``.

Covers ``Attributes`` -- the flat name store attached to ``Context``. Its only
surface is the binding operations (``let`` / ``set`` / ``exists``) and the
reads (``get`` / ``items``); copying is ``Context.branch``.
"""

from __future__ import annotations

import pytest

from nu.lang import EMPTY
from nu.lang.runtime.context.attributes import Attributes


# --- construction ---------------------------------------------------------


def test_empty_construction() -> None:
    assert dict(Attributes().items()) == {}


def test_construction_from_dict() -> None:
    attrs = Attributes({"a": 1, "b": "two"})
    assert attrs.get("a") == 1
    assert attrs.get("b") == "two"


# --- no raw store ---------------------------------------------------------


def test_item_access_is_not_a_way_in() -> None:
    attrs = Attributes({"x": 1})
    with pytest.raises(TypeError):
        _ = attrs["x"]  # type: ignore[index]
    with pytest.raises(TypeError):
        attrs["x"] = 2  # type: ignore[index]
    with pytest.raises(TypeError):
        del attrs["x"]  # type: ignore[attr-defined]


# --- get / items ----------------------------------------------------------


def test_get_returns_value() -> None:
    attrs = Attributes({"x": 5})
    assert attrs.get("x") == 5


def test_get_defaults_to_empty_when_undeclared() -> None:
    attrs = Attributes()
    assert attrs.get("missing") is EMPTY
    assert attrs.get("missing", "default") == "default"


def test_items_lists_every_declared_name() -> None:
    attrs = Attributes({"a": 1})
    with attrs.let("b", 2):
        assert dict(attrs.items()) == {"a": 1, "b": 2}
    assert dict(attrs.items()) == {"a": 1}


# --- repr -----------------------------------------------------------------


def test_repr_empty() -> None:
    assert repr(Attributes()) == "Attributes()"


def test_repr_includes_items() -> None:
    r = repr(Attributes({"x": 1}))
    assert "x" in r
    assert "1" in r


# --- binding: let / set / exists ------------------------------------------


def test_let_declares_the_name_for_the_scope_only() -> None:
    attrs = Attributes()
    with attrs.let("n", 1):
        assert attrs.get("n") == 1
    assert not attrs.exists("n")


def test_let_shadows_and_restores_the_outer_binding() -> None:
    attrs = Attributes()
    with attrs.let("n", 1):
        with attrs.let("n", 2):
            assert attrs.get("n") == 2
        assert attrs.get("n") == 1
    assert not attrs.exists("n")


def test_let_restores_on_error() -> None:
    attrs = Attributes()
    with attrs.let("n", 1):
        with pytest.raises(ValueError, match="boom"), attrs.let("n", 2):
            raise ValueError("boom")
        assert attrs.get("n") == 1
    assert not attrs.exists("n")


def test_let_restores_an_outer_empty_like_value() -> None:
    # A declared name holding None is still declared, and comes back as None.
    attrs = Attributes()
    with attrs.let("n", None):
        with attrs.let("n", 5):
            pass
        assert attrs.exists("n")
        assert attrs.get("n") is None


def test_let_refuses_a_name_that_is_not_a_str() -> None:
    with pytest.raises(TypeError, match="must be a str, got int"):
        Attributes().let(1, "v")


def test_set_reassigns_the_innermost_binding() -> None:
    attrs = Attributes()
    with attrs.let("n", 1):
        with attrs.let("n", 2):
            attrs.set("n", 3)
            assert attrs.get("n") == 3
        assert attrs.get("n") == 1


def test_set_on_an_undeclared_name_raises_with_a_let_hint() -> None:
    attrs = Attributes()
    with pytest.raises(NameError, match=r"'n'.*not declared.*attrs\.let"):
        attrs.set("n", 1)
    assert not attrs.exists("n")


def test_exists_means_declared() -> None:
    attrs = Attributes()
    assert attrs.exists("n") is False
    with attrs.let("n", None):
        assert attrs.exists("n") is True
    assert attrs.exists("n") is False


def test_let_held_by_a_generator_lives_across_its_yields() -> None:
    attrs = Attributes()

    def stream():
        with attrs.let("n", "bound"):
            yield attrs.get("n")
            yield attrs.get("n")

    gen = stream()
    assert next(gen) == "bound"
    assert attrs.get("n") == "bound"  # alive between pulls
    gen.close()
    assert not attrs.exists("n")  # released on close


def test_let_held_by_a_generator_releases_on_exhaustion() -> None:
    attrs = Attributes({"n": "outer"})

    def stream():
        with attrs.let("n", "inner"):
            yield from (1, 2)

    assert list(stream()) == [1, 2]
    assert attrs.get("n") == "outer"


async def test_let_held_by_an_async_generator_releases_on_close() -> None:
    attrs = Attributes({"n": "outer"})

    async def stream():
        with attrs.let("n", "inner"):
            yield 1
            yield 2

    agen = stream()
    assert await agen.__anext__() == 1
    assert attrs.get("n") == "inner"
    await agen.aclose()
    assert attrs.get("n") == "outer"
