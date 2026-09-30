"""Unit tests for ``nu.lang.runtime.context.attributes``.

Covers ``Attributes`` -- the flat mutable key-value store attached to
``Context``. Read/write surface, ``copy`` semantics across scope boundaries,
``copy_shallow`` semantics for a concurrent branch.
"""

from __future__ import annotations

import threading

import pytest

from nu.lang.runtime.context.attributes import Attributes


# --- construction ---------------------------------------------------------


def test_empty_construction() -> None:
    attrs = Attributes()
    assert len(attrs) == 0
    assert bool(attrs) is False


def test_construction_from_dict() -> None:
    attrs = Attributes({"a": 1, "b": "two"})
    assert attrs["a"] == 1
    assert attrs["b"] == "two"
    assert len(attrs) == 2


# --- read / write / delete ------------------------------------------------


def test_setitem_stores_value() -> None:
    attrs = Attributes()
    attrs["key"] = "value"
    assert attrs["key"] == "value"


def test_getitem_missing_raises_key_error() -> None:
    attrs = Attributes()
    with pytest.raises(KeyError):
        _ = attrs["missing"]


def test_delitem_removes_key() -> None:
    attrs = Attributes({"x": 1})
    del attrs["x"]
    assert "x" not in attrs
    assert len(attrs) == 0


def test_delitem_missing_raises_key_error() -> None:
    attrs = Attributes()
    with pytest.raises(KeyError):
        del attrs["missing"]


def test_contains() -> None:
    attrs = Attributes({"x": 1})
    assert "x" in attrs
    assert "y" not in attrs


def test_len_tracks_size() -> None:
    attrs = Attributes()
    assert len(attrs) == 0
    attrs["a"] = 1
    attrs["b"] = 2
    assert len(attrs) == 2
    del attrs["a"]
    assert len(attrs) == 1


def test_bool_reflects_emptiness() -> None:
    attrs = Attributes()
    assert not attrs
    attrs["x"] = 1
    assert attrs


# --- get ------------------------------------------------------------------


def test_get_returns_value() -> None:
    attrs = Attributes({"x": 5})
    assert attrs.get("x") == 5


def test_get_returns_default_when_missing() -> None:
    attrs = Attributes()
    assert attrs.get("missing") is None
    assert attrs.get("missing", "default") == "default"


# --- views ----------------------------------------------------------------


def test_keys_values_items() -> None:
    attrs = Attributes({"a": 1, "b": 2})
    assert set(attrs.keys()) == {"a", "b"}
    assert set(attrs.values()) == {1, 2}
    assert set(attrs.items()) == {("a", 1), ("b", 2)}


# --- copy: deep semantics -------------------------------------------------


def test_copy_returns_independent_attributes() -> None:
    attrs = Attributes({"x": 1})
    other = attrs.copy()
    assert other is not attrs
    other["y"] = 2
    assert "y" not in attrs


def test_copy_deep_copies_mutable_values() -> None:
    attrs = Attributes({"k": [1, 2]})
    other = attrs.copy()
    other["k"].append(3)
    assert attrs["k"] == [1, 2]
    assert other["k"] == [1, 2, 3]


def test_copy_of_empty_is_empty() -> None:
    attrs = Attributes()
    other = attrs.copy()
    assert len(other) == 0
    assert other is not attrs


# --- copy_shallow: branch semantics ---------------------------------------


def test_copy_shallow_gives_its_own_key_space() -> None:
    attrs = Attributes({"x": 1})
    other = attrs.copy_shallow()
    other["x"] = 2
    other["y"] = 3
    assert attrs["x"] == 1
    assert "y" not in attrs


def test_copy_shallow_shares_values_by_reference() -> None:
    attrs = Attributes({"k": [1, 2]})
    other = attrs.copy_shallow()
    other["k"].append(3)
    assert attrs["k"] is other["k"]
    assert attrs["k"] == [1, 2, 3]


def test_copy_shallow_carries_an_unpicklable_value() -> None:
    # What ``copy`` cannot do: a lock (or a live task) has no deepcopy.
    lock = threading.Lock()
    attrs = Attributes({"lock": lock})
    assert attrs.copy_shallow()["lock"] is lock


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
        assert attrs["n"] == 1
    assert "n" not in attrs


def test_let_shadows_and_restores_the_outer_binding() -> None:
    attrs = Attributes()
    with attrs.let("n", 1):
        with attrs.let("n", 2):
            assert attrs["n"] == 2
        assert attrs["n"] == 1
    assert "n" not in attrs


def test_let_restores_on_error() -> None:
    attrs = Attributes()
    with attrs.let("n", 1):
        with pytest.raises(ValueError, match="boom"), attrs.let("n", 2):
            raise ValueError("boom")
        assert attrs["n"] == 1
    assert "n" not in attrs


def test_let_restores_an_outer_empty_like_value() -> None:
    # A declared name holding None is still declared, and comes back as None.
    attrs = Attributes()
    with attrs.let("n", None):
        with attrs.let("n", 5):
            pass
        assert attrs.exists("n")
        assert attrs["n"] is None


def test_let_refuses_a_name_that_is_not_a_str() -> None:
    with pytest.raises(TypeError, match="must be a str, got int"):
        Attributes().let(1, "v")


def test_set_reassigns_the_innermost_binding() -> None:
    attrs = Attributes()
    with attrs.let("n", 1):
        with attrs.let("n", 2):
            attrs.set("n", 3)
            assert attrs["n"] == 3
        assert attrs["n"] == 1


def test_set_on_an_undeclared_name_raises_with_a_let_hint() -> None:
    attrs = Attributes()
    with pytest.raises(NameError, match=r"not declared.*nu\.Let\('n'"):
        attrs.set("n", 1)
    assert "n" not in attrs


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
            yield attrs["n"]
            yield attrs["n"]

    gen = stream()
    assert next(gen) == "bound"
    assert attrs["n"] == "bound"  # alive between pulls
    gen.close()
    assert "n" not in attrs  # released on close


def test_let_held_by_a_generator_releases_on_exhaustion() -> None:
    attrs = Attributes({"n": "outer"})

    def stream():
        with attrs.let("n", "inner"):
            yield from (1, 2)

    assert list(stream()) == [1, 2]
    assert attrs["n"] == "outer"


async def test_let_held_by_an_async_generator_releases_on_close() -> None:
    attrs = Attributes({"n": "outer"})

    async def stream():
        with attrs.let("n", "inner"):
            yield 1
            yield 2

    agen = stream()
    assert await agen.__anext__() == 1
    assert attrs["n"] == "inner"
    await agen.aclose()
    assert attrs["n"] == "outer"
