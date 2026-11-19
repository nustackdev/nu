"""A mem write stores its own copy of plain containers.

Setting a slot from a Literal dict used to store the Literal's own dict, so
an item write through the slot changed the term and carried into the next
run. The same held for lists, sets and nested containers, and for a dict the
caller passed in.
"""

from __future__ import annotations

import nu


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
