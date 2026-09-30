"""Tests for the Context fabric: attrs ref read, ``.set()`` write.

An attrs ref reads its slot in ``ctx.attrs``; ``.set()`` reassigns it through
the Ref. Together they are the keystone state path: a value written under an
address is read back under that address. The write goes through ``ref._write``,
never by the Command touching ``ctx.attrs`` itself, and only reaches a name
that is already declared.

The address is just a Nu child, so it can be computed: ``ObjectRef(StrRef("key"))``
reads ``ctx.attrs`` under whatever value ``ctx.attrs.get("key")`` holds - read and
write both resolve the address through the runtime.
"""

from __future__ import annotations

import pytest

from nu.context import IntRef, ObjectRef, StrRef
from nu.context.attrs import AttrRef
from nu.core import Add
from nu.lang import INVALID, Attr, Context, Effect, Literal
from nu.lang.helpers import arun, compile, run


# --- read ----------------------------------------------------------------


def test_attrref_reads_a_bound_slot():
    ctx = Context(attrs={"x": 7})
    value, _ = run(Add(ObjectRef("x"), Literal(1)), ctx)
    assert value == 8


def test_attrref_on_an_unbound_address_is_empty_and_propagates():
    value, _ = run(Add(ObjectRef("missing"), Literal(1)))
    assert value is INVALID


# --- .set() ----------------------------------------------------------------


def test_set_writes_through_the_ref():
    ctx = Context(attrs={"total": 0})
    _, ctx = run(IntRef("total").set(Literal(5)), ctx)
    assert ctx.attrs.get("total") == 5


def test_set_reads_then_writes_the_same_slot():
    ctx = Context(attrs={"total": 10})
    total = IntRef("total")
    run(total.set(total + 1), ctx)
    assert ctx.attrs.get("total") == 11


def test_set_does_not_store_a_sentinel():
    ctx = Context(attrs={"y": 1})
    run(IntRef("y").set(Add(ObjectRef("missing"), Literal(1))), ctx)
    assert ctx.attrs.get("y") == 1


def test_set_on_an_undeclared_name_raises():
    with pytest.raises(NameError, match=r"nu\.Let"):
        run(IntRef("total").set(5))


# --- computed address: the address is a Nu child -------------------------


def test_attrref_reads_a_computed_address_slot():
    ctx = Context(attrs={"key": "total", "total": 5})
    # ObjectRef(StrRef("key")) reads the name held at "key", which is "total".
    value, _ = run(Add(ObjectRef(StrRef("key")), Literal(1)), ctx)
    assert value == 6


def test_set_writes_through_a_computed_address():
    ctx = Context(attrs={"key": "total", "total": 0})
    _, ctx = run(ObjectRef(StrRef("key")).set(Literal(9)), ctx)
    assert ctx.attrs.get("total") == 9


async def test_computed_address_resolves_on_the_async_path():
    ctx = Context(attrs={"key": "total", "total": 0})
    _, ctx = await arun(ObjectRef(StrRef("key")).set(Literal(4)), ctx)
    assert ctx.attrs.get("total") == 4


async def test_set_on_an_undeclared_name_raises_on_the_async_path():
    with pytest.raises(NameError, match=r"nu\.Let"):
        await arun(IntRef("total").set(5))


# --- .exists() -----------------------------------------------------------


def test_attr_exists_is_true_for_a_bound_address():
    ctx = Context(attrs={"total": 0})
    value, _ = run(ObjectRef("total").exists(), ctx)
    assert value is True


def test_attr_exists_is_false_for_an_unbound_address():
    value, _ = run(ObjectRef("missing").exists())
    assert value is False


def test_attr_exists_distinguishes_a_bound_empty_from_missing():
    # A read yields EMPTY for an unbound address; exists separates the two cases.
    ctx = Context(attrs={"here": None})
    value, _ = run(ObjectRef("here").exists(), ctx)
    assert value is True


# --- effects -------------------------------------------------------------


def test_attr_exists_reads_its_ref_fabric():
    program = compile(ObjectRef("total").exists())
    effects = program.attr(program.root, Attr.COMPOSITION_EFFECTS)
    assert effects == frozenset({(ObjectRef, Effect.READ)})
    assert all(isinstance(ref, AttrRef) for ref in [ObjectRef("total")])
