"""Literal: the leaf where nu meets python.

``Literal(value)`` hands its value out as is, except the native mutable
containers, copied on each evaluation (the mutable default argument trap,
closed for the builtins). A container holding a term raises, an unhashable
instance warns. ``Literal(factory=f, **kwargs)`` runs its kwargs as children
and builds ``f(**values)`` fresh on every run.
"""

from __future__ import annotations

import asyncio
import functools
import math
import warnings

import pytest

import nu
from nu.engine.validation.law import ValidationError
from nu.lang import Cardinality, MutableLiteralWarning, Sort, wire
from nu.lang.attributes import Attr, Effect
from nu.lang.helpers import compile


class Cfg(nu.Shape):
    kwargs = nu.DictRef.slot(nu.StrRef)
    nested = nu.DictRef.slot(object)
    nums = nu.ListRef.slot(nu.IntRef)
    tags = nu.SetRef.slot(nu.StrRef)


class _Handle:
    """A live object: hashable by identity, so a Literal carries it as is."""


class _Mutable:
    """An unhashable instance: defines ``__eq__`` and no ``__hash__``."""

    def __eq__(self, other: object) -> bool:
        return other is self


# --- the plain form: as is ----------------------------------------------------


def test_a_plain_value_is_handed_out_as_is() -> None:
    handle, term = _Handle(), nu.Literal(1)
    for value in (handle, term, (1, "s", b"b"), frozenset({1}), ValueError, len, math):
        assert nu.run(nu.Literal(value))[0] is value
        assert asyncio.run(nu.arun(nu.Literal(value)))[0] is value


def test_a_builtin_subclass_is_not_copied() -> None:
    class Bag(list):
        __hash__ = object.__hash__

    bag = Bag([1])
    assert nu.run(nu.Literal(bag))[0] is bag


# --- the plain form: native containers copied ---------------------------------


def test_each_evaluation_gives_a_new_container() -> None:
    lit = nu.Literal({"a": [1], "b": {2}, "c": bytearray(b"x")})
    first, second = nu.run(lit)[0], nu.run(lit)[0]
    assert first == second == lit.value
    assert first is not lit.value
    assert first is not second
    for key in ("a", "b", "c"):
        assert first[key] is not lit.value[key]


def test_the_async_path_copies_too() -> None:
    lit = nu.Literal([1, [2]])
    first, second = (asyncio.run(nu.arun(lit))[0] for _ in range(2))
    assert first == second == [1, [2]]
    assert first is not lit.value
    assert first[1] is not lit.value[1]
    assert first is not second


def test_containers_inside_a_tuple_are_copied() -> None:
    inner: list = [1]
    lit = nu.Literal((inner, 2))
    out = nu.run(lit)[0]
    assert out == ([1], 2)
    assert out[0] is not inner
    assert asyncio.run(nu.arun(lit))[0][0] is not inner


def test_a_live_object_inside_keeps_its_identity() -> None:
    handle = _Handle()
    out = nu.run(nu.Literal({"h": handle, "deep": [(handle, [1])]}))[0]
    assert out["h"] is handle
    assert out["deep"][0][0] is handle


def test_what_a_run_does_to_the_value_never_reaches_the_program() -> None:
    lit = nu.Literal({"name": "a"})
    nu.run(nu.let(Cfg, Cfg.kwargs.set(lit) >> Cfg.kwargs["name"].set("b")))
    assert lit.value == {"name": "a"}
    nums, tags = nu.Literal([1]), nu.Literal({"a"})
    nu.run(nu.let(Cfg, Cfg.nums.set(nums) >> Cfg.nums.append(9)))
    nu.run(nu.let(Cfg, Cfg.tags.set(tags) >> Cfg.tags.add("z")))
    assert nums.value == [1]
    assert tags.value == {"a"}


def test_a_nested_container_is_copied_too() -> None:
    lit = nu.Literal({"inner": {"k": "a"}})
    inner = Cfg.nested["inner"].to(nu.DictRef.slot(str))
    nu.run(nu.let(Cfg, Cfg.nested.set(lit) >> inner["k"].set("b")))
    assert lit.value == {"inner": {"k": "a"}}


def test_the_callers_dict_is_not_changed() -> None:
    src = {"name": "a"}
    nu.run(nu.let(Cfg, Cfg.kwargs.set(src) >> Cfg.kwargs["name"].set("b")))
    assert src == {"name": "a"}


def test_a_frame_seed_with_an_item_write_starts_from_a_on_every_run(capsys) -> None:
    name = Cfg.kwargs["name"]
    tree = nu.let(Cfg, name.set(name + "b") >> nu.print(name), kwargs={"name": "a"})
    before = repr(tree)
    nu.run(tree)
    nu.run(tree)
    asyncio.run(nu.arun(tree))
    assert capsys.readouterr().out == "ab\nab\nab\n"
    assert repr(tree) == before


def test_the_store_still_sees_its_own_writes() -> None:
    data: dict = {}
    ctx = nu.Context().bind(dict, data, Cfg)
    nu.run(Cfg.kwargs.set({"name": "a"}) >> Cfg.kwargs["name"].set("b"), ctx)
    assert data == {"kwargs": {"name": "b"}}


# --- the plain form: a container holding a term raises ------------------------


@pytest.mark.parametrize(
    "value",
    [
        {"x": nu.Literal(1)},
        [1, [nu.Add(1, 2)]],
        (1, {"deep": nu.Literal(2)}),
        {nu.Literal(1)},
        frozenset({nu.Literal(1)}),
        {nu.Literal("k"): 1},
    ],
    ids=["dict", "nested-list", "tuple", "set", "frozenset", "dict-key"],
)
def test_a_container_holding_a_term_raises(value: object) -> None:
    with pytest.raises(TypeError, match=r"Literal\(factory="):
        nu.Literal(value)


def test_an_auto_wrapped_container_holding_a_term_raises() -> None:
    with pytest.raises(TypeError, match=r"Dict\.of"):
        nu.print({"x": nu.Add(1, 2)})


def test_a_term_itself_is_quoted_as_data() -> None:
    body = nu.Add(1, 2)
    assert nu.run(nu.Literal(body))[0] is body


# --- the plain form: an unhashable instance warns -----------------------------


def test_an_unhashable_instance_warns_and_is_handed_out_as_is() -> None:
    obj = _Mutable()
    with pytest.warns(MutableLiteralWarning, match=r"Literal\(factory=_Mutable"):
        lit = nu.Literal(obj)
    assert nu.run(lit)[0] is obj


def test_the_warning_points_at_the_users_line() -> None:
    with pytest.warns(MutableLiteralWarning) as caught:
        nu.print(_Mutable())
    assert caught[0].filename == __file__


def test_terms_classes_functions_and_modules_never_warn() -> None:
    with warnings.catch_warnings():
        warnings.simplefilter("error", MutableLiteralWarning)
        for value in (nu.Literal(1), nu.Add(1, 2), _Mutable, dict, len, print, math, _Handle()):
            nu.Literal(value)
        nu.Literal(functools.partial(len))
        nu.Literal({"a": [1]})


# --- the factory form -----------------------------------------------------------


def test_a_factory_builds_a_fresh_value_on_every_run() -> None:
    lit = nu.Literal(factory=list)
    first, second = nu.run(lit)[0], nu.run(lit)[0]
    assert first == second == []
    assert first is not second
    a, b = (asyncio.run(nu.arun(lit))[0] for _ in range(2))
    assert a == [] and a is not b


def test_a_factory_runs_its_kwargs() -> None:
    lit = nu.Literal(factory=dict, x=12, y=nu.Add(1, 2), z=nu.Literal(factory=list))
    assert nu.run(lit)[0] == {"x": 12, "y": 3, "z": []}
    assert asyncio.run(nu.arun(lit))[0] == {"x": 12, "y": 3, "z": []}


def test_a_factory_matches_dict_of() -> None:
    data = {"kwargs": {"name": "a"}}
    ctx = nu.Context().bind(dict, data, Cfg)
    read = Cfg.kwargs["name"]
    lit = nu.Literal(factory=dict, x=12, y=read)
    assert nu.run(lit, ctx)[0] == nu.run(nu.Dict.of(x=12, y=read), ctx)[0] == {"x": 12, "y": "a"}


def test_a_factory_kwarg_computed_from_a_mem_read() -> None:
    name = Cfg.kwargs["name"]
    seen = nu.let(
        Cfg,
        nu.Literal(factory=lambda who: f"hi {who}", who=name),
        kwargs={"name": "a"},
    )
    assert nu.run(seen)[0] == "hi a"


def test_a_factory_folds_its_childrens_effects() -> None:
    pure = compile(nu.Literal(factory=dict, x=1))
    assert pure.attr((), Attr.COMPOSITION_EFFECTS) == frozenset()
    reading = compile(nu.Literal(factory=dict, x=Cfg.kwargs["name"]))
    effects = reading.attr((), Attr.COMPOSITION_EFFECTS)
    assert {effect for _, effect in effects} == {Effect.READ}
    assert reading.attr((), Attr.SORT) == Sort.SCALAR_QUERY
    assert reading.attr((), Attr.CARDINALITY) == Cardinality.SCALAR


def test_a_factory_refuses_a_stream_kwarg() -> None:
    with pytest.raises(ValidationError):
        nu.run(nu.Literal(factory=list, items=nu.Iter([1, 2])))


def test_value_and_factory_together_raise() -> None:
    with pytest.raises(TypeError, match="not both"):
        nu.Literal([1], factory=list)


def test_a_factory_must_be_callable() -> None:
    with pytest.raises(TypeError, match="callable"):
        nu.Literal(factory=42)


def test_an_async_factory_raises() -> None:
    async def build() -> dict:
        return {}

    with pytest.raises(TypeError, match=r"nu\.host"):
        nu.Literal(factory=build)


def test_kwargs_without_a_factory_raise() -> None:
    with pytest.raises(TypeError, match="no factory"):
        nu.Literal(x=1)
    with pytest.raises(TypeError, match="needs a value"):
        nu.Literal()


# --- fields, render, equal, wire ----------------------------------------------


def test_fields_of_both_forms() -> None:
    assert nu.tree.fields(nu.Literal(42)) == {"value": 42}
    lit = nu.Literal(factory=dict, x=1, y=2)
    assert nu.tree.fields(lit) == {"factory": dict, "keys": ("x", "y")}
    assert len(nu.tree.children(lit)) == 2


def test_render_shows_both_forms() -> None:
    assert repr(nu.Literal(42)) == "42"
    lit = nu.Literal(factory=dict, x=1, y=nu.Add(1, 2))
    assert repr(lit) == "Literal(factory=dict, x=1, y=Add(1, 2))"
    assert str(lit).splitlines()[0] == "Literal(factory=dict, x, y)"


def test_equal_compares_both_forms() -> None:
    assert nu.tree.equal(nu.Literal({"a": 1}), nu.Literal({"a": 1}))
    assert not nu.tree.equal(nu.Literal(1), nu.Literal(2))
    a = nu.Literal(factory=dict, x=1, y=nu.Add(1, 2))
    assert nu.tree.equal(a, nu.Literal(factory=dict, x=1, y=nu.Add(1, 2)))
    assert not nu.tree.equal(a, nu.Literal(factory=dict, x=1, z=nu.Add(1, 2)))
    assert not nu.tree.equal(a, nu.Literal(factory=list))
    assert not nu.tree.equal(nu.Literal(factory=list), nu.Literal(list))


def test_both_forms_cross_the_wire() -> None:
    for lit in (nu.Literal({"a": [1]}), nu.Literal(factory=dict, x=1, y=nu.Add(1, 2))):
        back = wire.loads(wire.dumps(lit))
        assert nu.tree.equal(back, lit)
        assert nu.run(back)[0] == nu.run(lit)[0]
    fresh = wire.loads(wire.dumps(nu.Literal(factory=list)))
    assert nu.run(fresh)[0] is not nu.run(fresh)[0]
