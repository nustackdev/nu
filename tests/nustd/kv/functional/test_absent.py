"""Absent addresses on kv refs: NULL reads, honest existence, writes that create.

A leaf read with nothing there gives NULL hinted with the dotted path. A
container ref gives a lazy handle, never NULL, so ``exists()`` is the question
to ask of it (one marker read). Writes and subscriptions on absent containers
work as on present ones.

A never-written container is not an empty one: ``len``, iteration and
``contains`` raise, ``extract()`` gives NULL, removals act as on an empty
container and create nothing.
"""

from __future__ import annotations

import asyncio

import pytest

import nu
from nu import Shape, arun, run
from nu.lang import is_null
from nustd.kv import (
    BoolRef,
    DictRef,
    IntRef,
    ListRef,
    SetRef,
    ShapeRef,
    Snapshot,
    StrRef,
    Transaction,
    memory_navigator,
)


class Inner(Shape):
    tags = ListRef.slot(str)
    meta = DictRef.slot(int)
    label = StrRef.slot()


class Root(Shape):
    tags = ListRef.slot(str)
    meta = DictRef.slot(int)
    names = SetRef.slot(str)
    inner = ShapeRef.slot(Inner)
    count = IntRef.slot()
    live = BoolRef.slot()


CONTAINERS = {
    "root_list": (Root.tags, ["a"]),
    "root_dict": (Root.meta, {"a": 1}),
    "root_set": (Root.names, {"a"}),
    "nested_list": (Root.inner.tags, ["a"]),
    "nested_dict": (Root.inner.meta, {"a": 1}),
}
HINTS = {
    "root_list": "Root.tags",
    "root_dict": "Root.meta",
    "root_set": "Root.names",
    "nested_list": "Root.inner.tags",
    "nested_dict": "Root.inner.meta",
}
EMPTIES = {
    "root_list": [],
    "root_dict": {},
    "root_set": set(),
    "nested_list": [],
    "nested_dict": {},
}


# --- leaf reads ---------------------------------------------------------------


def test_an_absent_leaf_reads_null_named_by_its_path(ctx) -> None:
    got = run(Root.count, ctx)[0]
    assert is_null(got)
    assert repr(got) == "<NULL Root.count>"


def test_an_absent_nested_key_names_every_level(ctx) -> None:
    got = run(Root.inner.meta["x"], ctx)[0]
    assert repr(got) == "<NULL Root.inner.meta.x>"


def test_an_index_past_the_end_reads_null(ctx) -> None:
    run(Root.tags.append("a"), ctx)
    assert repr(run(Root.tags[3], ctx)[0]) == "<NULL Root.tags.3>"


def test_ops_on_an_absent_leaf_raise_like_python(ctx) -> None:
    with pytest.raises(TypeError):
        run(Root.count + 1, ctx)


def test_a_leaf_exists_once_written_even_when_falsy(ctx) -> None:
    assert run(Root.live.exists(), ctx)[0] is False
    assert run(Root.live.is_set_falsy(), ctx)[0] is False
    run(Root.live.set(False), ctx)
    assert run(Root.live.exists(), ctx)[0] is True
    assert run(Root.live.is_set_falsy(), ctx)[0] is True


# --- container existence ------------------------------------------------------


@pytest.mark.parametrize("name", CONTAINERS)
def test_a_never_written_container_does_not_exist(ctx, name) -> None:
    ref, _ = CONTAINERS[name]
    assert run(ref.exists(), ctx)[0] is False


@pytest.mark.parametrize("name", CONTAINERS)
def test_a_container_written_empty_exists(ctx, name) -> None:
    ref, _ = CONTAINERS[name]
    run(ref.set(EMPTIES[name]), ctx)
    assert run(ref.exists(), ctx)[0] is True
    assert run(ref.is_set_falsy(), ctx)[0] is True


@pytest.mark.parametrize("name", CONTAINERS)
def test_a_non_empty_container_exists(ctx, name) -> None:
    ref, value = CONTAINERS[name]
    run(ref.set(value), ctx)
    assert run(ref.exists(), ctx)[0] is True
    assert run(ref.is_set_falsy(), ctx)[0] is False


def test_a_nested_shape_exists_once_a_field_is_written(ctx) -> None:
    assert run(Root.inner.exists(), ctx)[0] is False
    run(Root.inner.label.set("x"), ctx)
    assert run(Root.inner.exists(), ctx)[0] is True


@pytest.mark.parametrize("name", CONTAINERS)
def test_init_writes_a_never_written_container(ctx, name) -> None:
    ref, value = CONTAINERS[name]
    run(ref.init(EMPTIES[name]), ctx)
    assert run(ref.exists(), ctx)[0] is True
    run(ref.set(value), ctx)
    run(ref.init(EMPTIES[name]), ctx)  # a second init leaves it alone
    assert run(ref.eager.extract(), ctx)[0] == value


# --- writes on absent containers ---------------------------------------------


@pytest.mark.parametrize(
    ("ref", "write", "want"),
    [
        (Root.tags, Root.tags.append("a"), ["a"]),
        (Root.names, Root.names.add("a"), {"a"}),
        (Root.meta, Root.meta["a"].set(1), {"a": 1}),
        (Root.meta, Root.meta.update({"a": 1}), {"a": 1}),
        (Root.inner.tags, Root.inner.tags.append("a"), ["a"]),
        (Root.inner.meta, Root.inner.meta["a"].set(1), {"a": 1}),
    ],
    ids=["append", "add", "set_item", "update", "nested_append", "nested_set_item"],
)
def test_a_write_creates_an_absent_container(ctx, ref, write, want) -> None:
    run(write, ctx)
    assert run(ref.exists(), ctx)[0] is True
    assert run(ref.eager.extract(), ctx)[0] == want


@pytest.mark.asyncio
async def test_a_subscription_on_an_absent_container_hears_the_first_write() -> None:
    heard: list = []

    @nu.host(base=nu.lang.ScalarAction, mutates=frozenset({0}))
    def keep(value: object) -> None:
        heard.append(value)

    tree = nu.With(
        memory_navigator(),
        body=nu.Gather(
            Snapshot(nu.ReactOnce(Root.inner.tags.on_children_change(), keep(True))),
            nu.DelayedDo(0.05, Transaction(Root.inner.tags.append("a"))),
        ),
    )
    await asyncio.wait_for(arun(tree), 5.0)
    assert heard == [True]


# --- reads that need the container ---------------------------------------------


@pytest.mark.parametrize("name", CONTAINERS)
def test_len_on_a_never_written_container_raises(ctx, name) -> None:
    ref, _ = CONTAINERS[name]
    with pytest.raises(KeyError):  # virtuals' own not-found error, a KeyError
        run(ref.len(), ctx)


@pytest.mark.parametrize("name", CONTAINERS)
def test_iter_on_a_never_written_container_raises(ctx, name) -> None:
    ref, _ = CONTAINERS[name]
    with pytest.raises(KeyError):
        run(nu.Collect(ref.iter()), ctx)


@pytest.mark.parametrize("name", CONTAINERS)
def test_contains_on_a_never_written_container_raises(ctx, name) -> None:
    ref, _ = CONTAINERS[name]
    with pytest.raises(KeyError):
        run(ref.contains("a"), ctx)


@pytest.mark.parametrize("name", CONTAINERS)
@pytest.mark.parametrize("facet", ["lazy", "eager"])
def test_extract_of_a_never_written_container_is_null(ctx, name, facet) -> None:
    ref, _ = CONTAINERS[name]
    got = run(getattr(ref, facet).extract(), ctx)[0]
    assert is_null(got)
    assert repr(got) == f"<NULL {HINTS[name]}>"


@pytest.mark.parametrize("name", CONTAINERS)
def test_extract_of_a_container_written_empty_is_its_empty_value(ctx, name) -> None:
    ref, _ = CONTAINERS[name]
    run(ref.set(EMPTIES[name]), ctx)
    assert run(ref.extract(), ctx)[0] == EMPTIES[name]


def test_a_container_ref_is_a_handle_never_null(ctx) -> None:
    assert not is_null(run(Root.inner.tags, ctx)[0])
    assert run(Root.inner.tags.exists(), ctx)[0] is False


def test_a_point_read_under_a_never_written_container_is_null(ctx) -> None:
    got = run(Root.inner.meta["a"], ctx)[0]
    assert is_null(got)
    assert repr(got) == "<NULL Root.inner.meta.a>"


# --- removals on absent containers ---------------------------------------------


@pytest.mark.parametrize(
    ("ref", "write"),
    [
        (Root.tags, Root.tags.clear()),
        (Root.names, Root.names.discard("a")),
        (Root.names, Root.names.clear()),
        (Root.meta, Root.meta.clear()),
        (Root.inner.tags, Root.inner.tags.clear()),
    ],
    ids=["list_clear", "discard", "set_clear", "dict_clear", "nested_clear"],
)
def test_a_removal_on_an_absent_container_creates_nothing(ctx, ref, write) -> None:
    run(write, ctx)
    assert run(ref.exists(), ctx)[0] is False


@pytest.mark.parametrize(
    ("ref", "write", "error"),
    [
        (Root.tags, Root.tags.eager.pop(), IndexError),
        (Root.tags, Root.tags.remove("a"), ValueError),
        (Root.names, Root.names.remove("a"), KeyError),
        (Root.meta, Root.meta.eager.pop("a"), KeyError),
    ],
    ids=["list_pop", "list_remove", "set_remove", "dict_pop"],
)
def test_a_removal_that_needs_an_item_raises_and_creates_nothing(ctx, ref, write, error) -> None:
    with pytest.raises(error):
        run(write, ctx)
    assert run(ref.exists(), ctx)[0] is False
