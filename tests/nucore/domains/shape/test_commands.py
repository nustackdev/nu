"""Tests for shape fabric write commands: SetCmd and Erase.

Covers class hierarchy, construction, and mutates declaration. Full execution
(ref.write / ref.aerase with a real substrate) is deferred.
"""

from __future__ import annotations

import pytest

from nu.domains.shape.interactions import Erase, PrimitiveSet, SetCmd
from nu.domains.shape.refs.item import ItemRef
from nu.lang import Command, Literal
from nu.lang.sentinels import EMPTY, INVALID


# ---------------------------------------------------------------------------
# Class hierarchy
# ---------------------------------------------------------------------------


def test_set_command_is_command():
    assert issubclass(SetCmd, Command)


def test_erase_command_is_command():
    assert issubclass(Erase, Command)


# ---------------------------------------------------------------------------
# Construction
# ---------------------------------------------------------------------------


def test_set_command_constructs_with_ref_and_value():
    ref = ItemRef("slot")
    cmd = SetCmd(ref, Literal(42))
    assert len(cmd._children) == 2


def test_erase_command_constructs_with_ref():
    ref = ItemRef("slot")
    cmd = Erase(ref)
    assert cmd._children


# ---------------------------------------------------------------------------
# mutates declaration
# ---------------------------------------------------------------------------


def test_set_command_mutates_slot_zero():
    mutates = SetCmd._attributes.get("mutates")
    assert mutates is not None
    assert 0 in mutates.value


def test_erase_command_mutates_slot_zero():
    mutates = Erase._attributes.get("mutates")
    assert mutates is not None
    assert 0 in mutates.value


# ---------------------------------------------------------------------------
# Substrate execution deferred
# ---------------------------------------------------------------------------


@pytest.mark.skip(reason="substrate impl deferred — SetCmd.compile needs ref.write")
def test_set_command_writes_value():
    pass


@pytest.mark.skip(reason="substrate impl deferred — Erase.compile needs ref.erase")
def test_erase_command_removes_slot():
    pass


# ---------------------------------------------------------------------------
# SetCmd sentinel raise (#7 — v1 parity)
# ---------------------------------------------------------------------------


def _make_thunk(value):
    def thunk(rt):
        return value

    return thunk


def test_set_command_thunk_raises_on_empty():
    ref = ItemRef("slot")
    cmd = SetCmd(ref, Literal(42))
    thunk = cmd._compile(0, (_make_thunk(None), _make_thunk(EMPTY)))
    with pytest.raises(ValueError, match="sentinel"):
        thunk(None)


def test_set_command_thunk_raises_on_invalid():
    ref = ItemRef("slot")
    cmd = SetCmd(ref, Literal(42))
    thunk = cmd._compile(0, (_make_thunk(None), _make_thunk(INVALID)))
    with pytest.raises(ValueError, match="sentinel"):
        thunk(None)


# ---------------------------------------------------------------------------
# PrimitiveSet (#5 — v1 parity)
# ---------------------------------------------------------------------------


def test_primitive_set_command_is_command():
    assert issubclass(PrimitiveSet, Command)


def test_primitive_set_command_constructs_with_ref_and_value():
    ref = ItemRef("slot")
    cmd = PrimitiveSet(ref, Literal({"a": 1}))
    assert len(cmd._children) == 2


def test_primitive_set_command_mutates_slot_zero():
    mutates = PrimitiveSet._attributes.get("mutates")
    assert mutates is not None
    assert 0 in mutates.value


def test_primitive_set_command_thunk_raises_on_empty():
    ref = ItemRef("slot")
    cmd = PrimitiveSet(ref, Literal(42))
    thunk = cmd._compile(0, (_make_thunk(None), _make_thunk(EMPTY)))
    with pytest.raises(ValueError, match="sentinel"):
        thunk(None)


def test_primitive_set_command_thunk_raises_on_invalid():
    ref = ItemRef("slot")
    cmd = PrimitiveSet(ref, Literal(42))
    thunk = cmd._compile(0, (_make_thunk(None), _make_thunk(INVALID)))
    with pytest.raises(ValueError, match="sentinel"):
        thunk(None)
