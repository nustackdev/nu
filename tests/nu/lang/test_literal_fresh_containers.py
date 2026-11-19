"""A Literal hands out a fresh copy of plain mutable containers each evaluation.

Setting a slot from a Literal dict used to store the Literal's own dict, so
an item write through the slot changed the term and carried into the next
run: a mutable default argument. The same held for lists, sets and nested
containers, and for a dict the caller passed in. The copy is made where the
program's value comes out, on evaluation, so every consumer is covered.
"""

from __future__ import annotations

import asyncio

import nu


def test_each_evaluation_gives_a_new_container() -> None:
    lit = nu.Literal({"a": [1]})
    first, second = nu.run(lit)[0], nu.run(lit)[0]
    assert first == second == {"a": [1]}
    assert first is not lit.value
    assert first is not second
    assert first["a"] is not lit.value["a"]


def test_the_async_path_copies_too() -> None:
    lit = nu.Literal([1, 2])
    out = asyncio.run(nu.arun(lit))[0]
    assert out == [1, 2]
    assert out is not lit.value


def test_containers_inside_a_tuple_are_copied() -> None:
    inner: list = [1]
    out = nu.run(nu.Literal((inner, 2)))[0]
    assert out == ([1], 2)
    assert out[0] is not inner


def test_everything_else_is_handed_out_as_is() -> None:
    class Bag(list):
        pass

    obj, bag, term = object(), Bag([1]), nu.Literal(1)
    plain = (1, "s", b"b", frozenset({1}))
    for value in (obj, bag, term, plain, ValueError):
        assert nu.run(nu.Literal(value))[0] is value


class Cfg(nu.Shape):
    kwargs = nu.DictRef.slot(nu.StrRef)
    nested = nu.DictRef.slot(object)
    nums = nu.ListRef.slot(nu.IntRef)
    tags = nu.SetRef.slot(nu.StrRef)


def test_a_frame_seed_is_not_changed_by_an_item_write() -> None:
    tree = nu.Frame(Cfg, Cfg.kwargs["name"].set("b"), kwargs={"name": "a"})
    before = repr(tree)
    nu.run(tree)
    nu.run(tree)
    assert repr(tree) == before
    assert "'name': 'a'" in before


def test_each_run_starts_from_the_literal_it_was_given() -> None:
    lit = nu.Literal({"name": "a"})
    tree = nu.Frame(Cfg, Cfg.kwargs.set(lit) >> Cfg.kwargs["name"].set("b"))
    nu.run(tree)
    assert lit.value == {"name": "a"}


def test_a_nested_container_is_owned_too() -> None:
    lit = nu.Literal({"inner": {"k": "a"}})
    nu.run(
        nu.Frame(
            Cfg, Cfg.nested.set(lit) >> Cfg.nested["inner"].to(nu.DictRef.slot(str))["k"].set("b")
        )
    )
    assert lit.value == {"inner": {"k": "a"}}


def test_lists_and_sets_are_owned() -> None:
    nums, tags = nu.Literal([1]), nu.Literal({"a"})
    nu.run(nu.Frame(Cfg, Cfg.nums.set(nums) >> Cfg.nums.append(9)))
    nu.run(nu.Frame(Cfg, Cfg.tags.set(tags) >> Cfg.tags.add("z")))
    assert nums.value == [1]
    assert tags.value == {"a"}


def test_the_callers_dict_is_not_changed() -> None:
    src = {"name": "a"}
    nu.run(nu.Frame(Cfg, Cfg.kwargs.set(src) >> Cfg.kwargs["name"].set("b")))
    assert src == {"name": "a"}


def test_the_store_still_sees_its_own_writes() -> None:
    data: dict = {}
    ctx = nu.Context().bind(dict, data, Cfg)
    nu.run(Cfg.kwargs.set({"name": "a"}) >> Cfg.kwargs["name"].set("b"), ctx)
    assert data == {"kwargs": {"name": "b"}}
