"""Tests for the Context fabric: AttrRef read, Set / Delete write.

AttrRef reads its slot in ``ctx.attrs``; Set and Delete write it through the
Ref. Together they are the keystone state path: a value written under a name is
read back under that name. The write goes through ``ref.write`` / ``ref.erase``,
never by the Command touching ``ctx.attrs`` itself.
"""

from __future__ import annotations

from nu2.context import AttrRef, Delete, Set
from nu2.core import Add, Literal
from nu2.lang import INVALID, Context
from nu2.lang.helpers import run


# --- AttrRef read --------------------------------------------------------


def test_attrref_reads_a_bound_slot():
    ctx = Context()
    ctx.attrs["x"] = 7
    value, _ = run(Add(AttrRef("x"), Literal(1)), ctx)
    assert value == 8


def test_attrref_on_an_unbound_name_is_empty_and_propagates():
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


def test_delete_of_an_unbound_name_is_a_noop():
    ctx = Context()
    run(Delete(AttrRef("absent")), ctx)
    assert "absent" not in ctx.attrs
