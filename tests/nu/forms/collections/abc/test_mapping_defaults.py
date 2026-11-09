"""Mapping reads with an explicit default: ``get_item(key, default)`` and ``pop(key, default)``.

The form forwards a given default to the runtime mapping's own ``get`` /
``pop``, as Python does. Any value is a default, None and NULL included; with
no default a missing key raises. Nothing turns into NULL on its own.
"""

from __future__ import annotations

import asyncio

import pytest

import nu
from nu.forms.collections.abc.mapping_interactions import DictPop, Get
from nu.lang import is_null
from nu.lang.literal import Literal


class _Recording(dict):
    """A dict that records how its ``get`` / ``pop`` were called."""

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.calls: list[tuple] = []

    def get(self, *args):  # type: ignore[override]
        self.calls.append(("get", *args))
        return super().get(*args)

    def pop(self, *args):  # type: ignore[override]
        self.calls.append(("pop", *args))
        return super().pop(*args)


def test_get_item_without_default_raises_on_a_missing_key() -> None:
    with pytest.raises(KeyError):
        nu.run(nu.Dict({"a": 1}).get_item("b"))


def test_get_item_default_is_any_value_none_included() -> None:
    d = nu.Dict({"a": 1})
    assert nu.run(d.get_item("a", 0))[0] == 1
    assert nu.run(d.get_item("b", 0))[0] == 0
    assert nu.run(d.get_item("b", None))[0] is None


def test_get_item_default_null_is_explicit() -> None:
    assert is_null(nu.run(nu.Dict({"a": 1}).get_item("b", nu.NullForm()))[0])


def test_pop_without_default_raises_on_a_missing_key() -> None:
    with pytest.raises(KeyError):
        nu.run(nu.Dict({"a": 1}).pop("b"))


def test_pop_default_is_any_value_none_and_null_included() -> None:
    d = nu.Dict({"a": 1})
    assert nu.run(d.pop("a", 0))[0] == 1
    assert nu.run(d.pop("b", 0))[0] == 0
    assert nu.run(d.pop("b", None))[0] is None
    assert is_null(nu.run(d.pop("b", nu.NullForm()))[0])


def test_a_default_is_forwarded_to_the_mappings_own_methods() -> None:
    target = _Recording({"a": 1})
    assert nu.run(Get(Literal(target), "b", None))[0] is None
    assert nu.run(DictPop(Literal(target), "b", 0))[0] == 0
    assert nu.run(DictPop(Literal(target), "a"))[0] == 1
    assert target.calls == [("get", "b", None), ("pop", "b", 0), ("pop", "a")]


def test_async_mirrors_sync() -> None:
    async def go() -> None:
        d = nu.Dict({"a": 1})
        assert (await nu.arun(d.get_item("b", None)))[0] is None
        assert is_null((await nu.arun(d.get_item("b", nu.NullForm())))[0])
        assert (await nu.arun(d.pop("b", 0)))[0] == 0
        with pytest.raises(KeyError):
            await nu.arun(d.get_item("b"))
        with pytest.raises(KeyError):
            await nu.arun(d.pop("b"))

    asyncio.run(go())
