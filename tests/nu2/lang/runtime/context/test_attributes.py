"""Unit tests for ``nu2.lang.runtime.context.attributes``.

Covers ``Attributes`` -- the flat mutable key-value store attached to
``Context``. Read/write surface, ``copy`` semantics across scope boundaries.
"""

from __future__ import annotations

import pytest

from nu2.lang.runtime.context.attributes import Attributes


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


# --- repr -----------------------------------------------------------------


def test_repr_empty() -> None:
    assert repr(Attributes()) == "Attributes()"


def test_repr_includes_items() -> None:
    r = repr(Attributes({"x": 1}))
    assert "x" in r
    assert "1" in r
