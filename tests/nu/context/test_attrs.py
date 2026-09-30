"""Tests for the Context fabric attrs axis: ``nu.context.Attr`` read, ``.exists()``.

An interaction binds its internal values in ``ctx.attrs`` for its body; the
tree only reads them, through ``nu.context.Attr(name)``. The address is a Nu child, so
it can be computed. Nothing in the tree writes attrs: the old write surface
(``Let``, attrs ``Set``, ``.set()``, the typed attrs refs) is gone.
"""

from __future__ import annotations

import pytest

import nu
import nu.context.attrs
from nu.core import Add
from nu.lang import EMPTY, INVALID, Attr, Context, Effect, Literal
from nu.lang.helpers import arun, compile, run


class Tally(nu.Shape):
    n = nu.mem.IntRef.slot()


# --- read ----------------------------------------------------------------


def test_attr_reads_a_seeded_name():
    value, _ = run(Add(nu.context.Attr("x"), Literal(1)), Context(attrs={"x": 7}))
    assert value == 8


def test_attr_on_an_unbound_name_is_empty_and_propagates():
    assert run(nu.context.Attr("missing"))[0] is EMPTY
    assert run(Add(nu.context.Attr("missing"), Literal(1)))[0] is INVALID


def test_attr_reads_what_map_bound_for_each_item():
    term = nu.Collect(nu.Map(nu.Iter([1, 2, 3]), Add(nu.context.Attr("item"), 1)))
    assert run(term)[0] == [2, 3, 4]


def test_attr_reads_what_foreachdo_bound_for_each_item():
    loop = nu.ForEachDo(nu.Iter([1, 2, 3]), Tally.n.set(Tally.n + nu.context.Attr("item")))
    data: dict = {"n": 0}
    run(loop, Context().bind(dict, data, Tally))
    assert data == {"n": 6}


def test_attr_reads_the_error_trycatch_bound():
    term = nu.TryCatch(nu.raise_(ValueError, "boom"), catch=nu.ToStr(nu.context.Attr("error")))
    assert run(term)[0] == "boom"


async def test_attr_reads_a_binding_on_the_async_path():
    term = nu.Collect(nu.Map(nu.Iter([1, 2]), Add(nu.context.Attr("item"), 10)))
    assert (await arun(term))[0] == [11, 12]


def test_the_binding_ends_with_the_binder():
    _, ctx = run(nu.Collect(nu.Map(nu.Iter([1]), nu.context.Attr("item"))))
    assert not ctx.attrs.exists("item")


# --- computed address: the address is a Nu child -------------------------


def test_attr_reads_a_computed_address():
    ctx = Context(attrs={"key": "total", "total": 5})
    value, _ = run(Add(nu.context.Attr(nu.context.Attr("key")), Literal(1)), ctx)
    assert value == 6


async def test_computed_address_resolves_on_the_async_path():
    ctx = Context(attrs={"key": "total", "total": 4})
    assert (await arun(nu.context.Attr(nu.context.Attr("key")), ctx))[0] == 4


# --- wrapping in a form ----------------------------------------------------


def test_a_reader_wraps_the_read_in_the_form_it_needs():
    term = nu.Collect(nu.Map(nu.Iter(["ab", "c"]), nu.Str(nu.context.Attr("item")).upper()))
    assert run(term)[0] == ["AB", "C"]


# --- .exists() -----------------------------------------------------------


def test_attr_exists_is_true_for_a_bound_name():
    term = nu.Collect(nu.Map(nu.Iter([1]), nu.context.Attr("item").exists()))
    assert run(term)[0] == [True]


def test_attr_exists_is_false_for_an_unbound_name():
    assert run(nu.context.Attr("missing").exists())[0] is False


def test_attr_exists_distinguishes_a_name_bound_to_empty_from_missing():
    value, _ = run(nu.context.Attr("here").exists(), Context(attrs={"here": EMPTY}))
    assert value is True


# --- effects -------------------------------------------------------------


def test_attr_exists_reads_its_ref_fabric():
    program = compile(nu.context.Attr("total").exists())
    effects = program.attr(program.root, Attr.COMPOSITION_EFFECTS)
    assert effects == frozenset({(nu.context.Attr, Effect.READ)})


# --- the write surface is gone ---------------------------------------------


@pytest.mark.parametrize("name", ["Let", "TupleRef", "FrozenSetRef"])
def test_the_removed_names_are_not_on_nu(name):
    assert not hasattr(nu, name)


@pytest.mark.parametrize(
    "name", ["IntRef", "StrRef", "FloatRef", "BoolRef", "BytesRef", "ObjectRef"]
)
def test_the_typed_ref_names_on_nu_are_the_mem_refs(name):
    assert getattr(nu, name) is getattr(nu.mem, name)


@pytest.mark.parametrize("name", ["Let", "Set", "AttrRef"])
def test_the_removed_names_are_not_on_the_attrs_module(name):
    assert not hasattr(nu.context.attrs, name)


@pytest.mark.parametrize("name", ["set", "slot"])
def test_attr_has_no_write_or_slot_surface(name):
    # On an instance the Object form turns any attribute into a ``GetAttr``, so
    # the surface is checked on the class.
    assert not hasattr(nu.context.Attr, name)
