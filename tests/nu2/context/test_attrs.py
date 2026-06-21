"""Tests for the Context fabric: AttrRef read, Set / Delete write.

AttrRef reads its slot in ``ctx.attrs``; Set and Delete write it through the
Ref. Together they are the keystone state path: a value written under an address
is read back under that address. The write goes through ``ref.write`` /
``ref.erase``, never by the Command touching ``ctx.attrs`` itself.

The address is just a Nu child, so it can be computed: ``AttrRef(AttrRef("key"))``
reads ``ctx.attrs`` under whatever value ``ctx.attrs["key"]`` holds - read,
write, and delete all resolve the address through the runtime.
"""

from __future__ import annotations

from nu2.context import AttrExists, AttrRef, Delete, Set
from nu2.core import Add, Literal
from nu2.lang import INVALID, Attr, Context, Effect, compile
from nu2.lang.helpers import arun, run


# --- AttrRef read --------------------------------------------------------


def test_attrref_reads_a_bound_slot():
    ctx = Context()
    ctx.attrs["x"] = 7
    value, _ = run(Add(AttrRef("x"), Literal(1)), ctx)
    assert value == 8


def test_attrref_on_an_unbound_address_is_empty_and_propagates():
    value, _ = run(Add(AttrRef("missing"), Literal(1)))
    assert value is INVALID


# --- Set -----------------------------------------------------------------


def test_set_writes_through_the_ref():
    ctx = Context()
    _, ctx = run(Set(AttrRef("total"), Literal(5)), ctx)
    assert ctx.attrs["total"] == 5


def test_set_reads_then_writes_the_same_slot():
    ctx = Context()
    ctx.attrs["total"] = 10
    run(Set(AttrRef("total"), Add(AttrRef("total"), Literal(1))), ctx)
    assert ctx.attrs["total"] == 11


def test_set_does_not_store_a_sentinel():
    ctx = Context()
    run(Set(AttrRef("y"), Add(AttrRef("missing"), Literal(1))), ctx)
    assert "y" not in ctx.attrs


# --- Delete --------------------------------------------------------------


def test_delete_removes_a_bound_slot():
    ctx = Context()
    ctx.attrs["k"] = "v"
    run(Delete(AttrRef("k")), ctx)
    assert "k" not in ctx.attrs


def test_delete_of_an_unbound_address_is_a_noop():
    ctx = Context()
    run(Delete(AttrRef("absent")), ctx)
    assert "absent" not in ctx.attrs


# --- computed address: the address is a Nu child -------------------------


def test_attrref_reads_a_computed_address_slot():
    ctx = Context()
    ctx.attrs["key"] = "total"
    ctx.attrs["total"] = 5
    # AttrRef(AttrRef("key")) reads ctx.attrs[ctx.attrs["key"]] == ctx.attrs["total"].
    value, _ = run(Add(AttrRef(AttrRef("key")), Literal(1)), ctx)
    assert value == 6


def test_set_writes_through_a_computed_address():
    ctx = Context()
    ctx.attrs["key"] = "total"
    _, ctx = run(Set(AttrRef(AttrRef("key")), Literal(9)), ctx)
    assert ctx.attrs["total"] == 9


def test_delete_removes_a_computed_address_slot():
    ctx = Context()
    ctx.attrs["key"] = "total"
    ctx.attrs["total"] = 5
    run(Delete(AttrRef(AttrRef("key"))), ctx)
    assert "total" not in ctx.attrs


async def test_computed_address_resolves_on_the_async_path():
    ctx = Context()
    ctx.attrs["key"] = "total"
    _, ctx = await arun(Set(AttrRef(AttrRef("key")), Literal(4)), ctx)
    assert ctx.attrs["total"] == 4


# --- AttrExists ----------------------------------------------------------


def test_attr_exists_is_true_for_a_bound_address():
    ctx = Context()
    ctx.attrs["total"] = 0
    value, _ = run(AttrExists(AttrRef("total")), ctx)
    assert value is True


def test_attr_exists_is_false_for_an_unbound_address():
    value, _ = run(AttrExists(AttrRef("missing")))
    assert value is False


def test_attr_exists_distinguishes_a_bound_empty_from_missing():
    # A read yields EMPTY for an unbound address; exists separates the two cases.
    ctx = Context()
    ctx.attrs["here"] = None
    value, _ = run(AttrRef("here").exists(), ctx)
    assert value is True


# --- effects -------------------------------------------------------------


def test_attr_exists_reads_its_ref_fabric():
    program = compile(AttrExists(AttrRef("total")))
    assert program.attr(program.root, Attr.COMPOSITION_EFFECTS) == frozenset(
        {(AttrRef, Effect.READ)}
    )
