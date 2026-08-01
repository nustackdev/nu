"""Tests for shape fabric write commands: SetCommand and EraseCommand.

Covers class hierarchy, construction, and mutates declaration. Full execution
(ref.write / ref.aerase with a real substrate) is deferred.
"""

from __future__ import annotations

import pytest

from nu.core import LiteralQuery
from nu.domains.shape.interactions import EraseCommand, PrimitiveSetCommand, SetCommand
from nu.domains.shape.refs.item import ItemRef
from nu.lang import Command
from nu.lang.sentinels import EMPTY, INVALID


# ---------------------------------------------------------------------------
# Class hierarchy
# ---------------------------------------------------------------------------


def test_set_command_is_command():
    assert issubclass(SetCommand, Command)


def test_erase_command_is_command():
    assert issubclass(EraseCommand, Command)


# ---------------------------------------------------------------------------
# Construction
# ---------------------------------------------------------------------------


def test_set_command_constructs_with_ref_and_value():
    ref = ItemRef("slot")
    cmd = SetCommand(ref, LiteralQuery(42))
    assert len(cmd._children) == 2


def test_erase_command_constructs_with_ref():
    ref = ItemRef("slot")
    cmd = EraseCommand(ref)
    assert cmd._children


# ---------------------------------------------------------------------------
# mutates declaration
# ---------------------------------------------------------------------------


def test_set_command_mutates_slot_zero():
    mutates = SetCommand._attributes.get("mutates")
    assert mutates is not None
    assert 0 in mutates.value


def test_erase_command_mutates_slot_zero():
    mutates = EraseCommand._attributes.get("mutates")
    assert mutates is not None
    assert 0 in mutates.value


# ---------------------------------------------------------------------------
# Substrate execution deferred
# ---------------------------------------------------------------------------


@pytest.mark.skip(reason="substrate impl deferred — SetCommand.compile needs ref.write")
def test_set_command_writes_value():
    pass


@pytest.mark.skip(reason="substrate impl deferred — EraseCommand.compile needs ref.erase")
def test_erase_command_removes_slot():
    pass


# ---------------------------------------------------------------------------
# SetCommand sentinel raise (#7 — v1 parity)
# ---------------------------------------------------------------------------


def _make_thunk(value):
    def thunk(rt):
        return value

    return thunk


def test_set_command_thunk_raises_on_empty():
    ref = ItemRef("slot")
    cmd = SetCommand(ref, LiteralQuery(42))
    thunk = cmd._compile(0, (_make_thunk(None), _make_thunk(EMPTY)))
    with pytest.raises(ValueError, match="sentinel"):
        thunk(None)


def test_set_command_thunk_raises_on_invalid():
    ref = ItemRef("slot")
    cmd = SetCommand(ref, LiteralQuery(42))
    thunk = cmd._compile(0, (_make_thunk(None), _make_thunk(INVALID)))
    with pytest.raises(ValueError, match="sentinel"):
        thunk(None)


# ---------------------------------------------------------------------------
# PrimitiveSetCommand (#5 — v1 parity)
# ---------------------------------------------------------------------------


def test_primitive_set_command_is_command():
    assert issubclass(PrimitiveSetCommand, Command)


def test_primitive_set_command_constructs_with_ref_and_value():
    ref = ItemRef("slot")
    cmd = PrimitiveSetCommand(ref, LiteralQuery({"a": 1}))
    assert len(cmd._children) == 2


def test_primitive_set_command_mutates_slot_zero():
    mutates = PrimitiveSetCommand._attributes.get("mutates")
    assert mutates is not None
    assert 0 in mutates.value


def test_primitive_set_command_thunk_raises_on_empty():
    ref = ItemRef("slot")
    cmd = PrimitiveSetCommand(ref, LiteralQuery(42))
    thunk = cmd._compile(0, (_make_thunk(None), _make_thunk(EMPTY)))
    with pytest.raises(ValueError, match="sentinel"):
        thunk(None)


def test_primitive_set_command_thunk_raises_on_invalid():
    ref = ItemRef("slot")
    cmd = PrimitiveSetCommand(ref, LiteralQuery(42))
    thunk = cmd._compile(0, (_make_thunk(None), _make_thunk(INVALID)))
    with pytest.raises(ValueError, match="sentinel"):
        thunk(None)
