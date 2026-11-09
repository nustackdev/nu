"""Extractable: core Extract asks a registered live handle for its plain data.

A fabric registers its handle types with ``nu.shape.Extractable``; ``Extract``
calls ``extract()`` on instances and yields any other read as it is. Core names
no fabric type and never probes for an ``extract`` attribute.
"""

from __future__ import annotations

import asyncio

import pytest

import nu
from nu.domains.shape.extractable import Extractable


class _Handle:
    """A live handle over a dict, standing in for a fabric's lazy view."""

    def __init__(self, data: dict) -> None:
        self._data = data

    def extract(self) -> dict:
        return dict(self._data)


Extractable.register(_Handle)


class _Unregistered:
    """Has an ``extract`` attribute but was never registered."""

    def extract(self) -> str:
        return "probed"


class _Owned(Extractable):
    def __init__(self, items: list) -> None:
        self._items = items

    def extract(self) -> list:
        return list(self._items)


def test_extractable_is_exported_from_the_shape_package():
    assert nu.shape.Extractable is Extractable


def test_extractable_is_abstract():
    with pytest.raises(TypeError):
        Extractable()  # type: ignore[abstract]


def test_a_registered_handle_is_extracted_through_a_form():
    handle = _Handle({"a": 1})
    out = nu.run(nu.Dict(nu.Literal(handle)).extract())[0]
    assert out == {"a": 1}
    assert out is not handle
    assert type(out) is dict


def test_a_subclass_is_extracted():
    assert nu.run(nu.List(nu.Literal(_Owned([1, 2]))).extract())[0] == [1, 2]


def test_a_plain_read_comes_back_as_it_is():
    data = {"a": 1}
    assert nu.run(nu.Dict(nu.Literal(data)).extract())[0] is data


def test_an_unregistered_value_is_not_probed():
    value = _Unregistered()
    assert nu.run(nu.Dict(nu.Literal(value)).extract())[0] is value


def test_null_passes_through():
    class Port(nu.Shape):
        meta = nu.DictRef.slot(int)

    ctx = nu.Context().bind(dict, {}, Port)
    assert nu.lang.is_null(nu.run(Port.meta.extract(), ctx)[0])


def test_the_async_path_extracts_too():
    term = nu.Dict(nu.Literal(_Handle({"b": 2}))).extract()
    out = asyncio.run(nu.arun(term))[0]
    assert out == {"b": 2}
