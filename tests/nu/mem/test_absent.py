"""Absent addresses on mem refs: NULL reads, and in-place writes that create.

A read with nothing there gives NULL named by the path. An in-place call on a
never-written container creates it empty first, so ``append`` needs no ``set``
ahead of it. Pure reads still do not create anything.
"""

from __future__ import annotations

import pytest

import nu
from nu.lang import is_null


class Inner(nu.Shape):
    tags = nu.ListRef.slot(str)


class Root(nu.Shape):
    tags = nu.ListRef.slot(str)
    meta = nu.DictRef.slot(int)
    names = nu.SetRef.slot(str)
    inner = nu.ShapeRef.slot(Inner)


def _ctx(data: dict) -> nu.Context:
    return nu.Context().bind(dict, data, Root)


def test_an_absent_container_reads_null_and_is_not_created() -> None:
    data: dict = {}
    got = nu.run(Root.inner.tags, _ctx(data))[0]
    assert is_null(got)
    assert repr(got) == "<NULL Root.inner.tags>"
    assert nu.run(Root.tags.exists(), _ctx(data))[0] is False
    assert data == {}


@pytest.mark.parametrize(
    ("write", "want"),
    [
        (Root.tags.append("a"), {"tags": ["a"]}),
        (Root.tags.extend(["a", "b"]), {"tags": ["a", "b"]}),
        (Root.names.add("a"), {"names": {"a"}}),
        (Root.meta.update({"a": 1}), {"meta": {"a": 1}}),
        (Root.inner.tags.append("a"), {"inner": {"tags": ["a"]}}),
    ],
    ids=["append", "extend", "add", "update", "nested_append"],
)
def test_an_in_place_write_creates_an_absent_container(write, want) -> None:
    data: dict = {}
    nu.run(write, _ctx(data))
    assert data == want


@pytest.mark.asyncio
async def test_an_in_place_write_creates_an_absent_container_async() -> None:
    data: dict = {}
    await nu.arun(Root.inner.tags.append("a"), _ctx(data))
    assert data == {"inner": {"tags": ["a"]}}


def test_an_in_place_write_still_refuses_a_null_operand() -> None:
    data: dict = {}
    with pytest.raises(ValueError, match="NULL"):
        nu.run(Root.tags.append(Root.inner.tags), _ctx(data))


@pytest.mark.parametrize(
    "write",
    [
        Root.tags.append(Root.inner.tags),
        Root.tags.insert(0, Root.inner.tags),
        Root.names.add(Root.inner.tags),
        Root.meta.update(Root.inner.tags),
        Root.meta.set_item("a", Root.inner.tags),
    ],
    ids=["append", "insert", "add", "update", "set_item"],
)
def test_a_refused_write_leaves_nothing_behind(write) -> None:
    data: dict = {}
    with pytest.raises(ValueError, match="NULL"):
        nu.run(write, _ctx(data))
    assert data == {}


@pytest.mark.parametrize(
    "write",
    [
        Root.tags.clear(),
        Root.tags.reverse(),
        Root.names.discard("a"),
        Root.names.clear(),
        Root.names.difference_update({"a"}),
        Root.meta.clear(),
        Root.inner.tags.clear(),
    ],
    ids=[
        "list_clear",
        "reverse",
        "discard",
        "set_clear",
        "difference_update",
        "dict_clear",
        "nested",
    ],
)
def test_a_removal_on_an_absent_container_is_a_no_op_and_creates_nothing(write) -> None:
    data: dict = {}
    nu.run(write, _ctx(data))
    assert data == {}


@pytest.mark.parametrize(
    ("write", "error"),
    [
        (Root.tags.pop(), IndexError),
        (Root.tags.remove("a"), ValueError),
        (Root.names.remove("a"), KeyError),
        (Root.names.pop(), KeyError),
        (Root.meta.pop("a"), KeyError),
        (Root.inner.tags.pop(), IndexError),
    ],
    ids=["list_pop", "list_remove", "set_remove", "set_pop", "dict_pop", "nested_pop"],
)
def test_a_removal_that_needs_an_item_raises_as_on_empty_and_creates_nothing(write, error) -> None:
    data: dict = {}
    with pytest.raises(error):
        nu.run(write, _ctx(data))
    assert data == {}


@pytest.mark.parametrize(
    "read",
    [Root.tags.len(), nu.Collect(Root.tags.iter()), Root.names.contains("a")],
    ids=["len", "iter", "contains"],
)
def test_reads_that_need_the_container_raise_naming_the_path(read) -> None:
    with pytest.raises(TypeError, match="NULL Root"):
        nu.run(read, _ctx({}))
