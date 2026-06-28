"""Tests for shape fabric write commands: StoreCommand and EraseCommand.

Covers class hierarchy, construction, and mutates declaration. Full execution
(ref.write / ref.aerase with a real substrate) is deferred.
"""

from __future__ import annotations

import pytest

from nu2.core import LiteralQuery
from nu2.domains.shape.interactions import EraseCommand, PrimitiveStoreCommand, StoreCommand
from nu2.domains.shape.refs.item import ItemRef
from nu2.lang import Command
from nu2.lang.sentinels import EMPTY, INVALID


# ---------------------------------------------------------------------------
# Class hierarchy
# ---------------------------------------------------------------------------


def test_store_command_is_command():
    assert issubclass(StoreCommand, Command)


def test_erase_command_is_command():
    assert issubclass(EraseCommand, Command)


# ---------------------------------------------------------------------------
# Construction
# ---------------------------------------------------------------------------


def test_store_command_constructs_with_ref_and_value():
    ref = ItemRef("slot")
    cmd = StoreCommand(ref, LiteralQuery(42))
    assert len(cmd.children) == 2


def test_erase_command_constructs_with_ref():
    ref = ItemRef("slot")
    cmd = EraseCommand(ref)
    assert cmd.children


# ---------------------------------------------------------------------------
# mutates declaration
# ---------------------------------------------------------------------------


def test_store_command_mutates_slot_zero():
    mutates = StoreCommand.attributes.get("mutates")
    assert mutates is not None
    assert 0 in mutates.value


def test_erase_command_mutates_slot_zero():
    mutates = EraseCommand.attributes.get("mutates")
    assert mutates is not None
    assert 0 in mutates.value


# ---------------------------------------------------------------------------
# Substrate execution deferred
# ---------------------------------------------------------------------------


@pytest.mark.skip(reason="substrate impl deferred — StoreCommand.compile needs ref.write")
def test_store_command_writes_value():
    pass


@pytest.mark.skip(reason="substrate impl deferred — EraseCommand.compile needs ref.erase")
def test_erase_command_removes_slot():
    pass


# ---------------------------------------------------------------------------
# StoreCommand sentinel raise (#7 — v1 parity)
# ---------------------------------------------------------------------------


def _make_thunk(value):
    def thunk(rt):
        return value

    return thunk


def test_store_command_thunk_raises_on_empty():
    ref = ItemRef("slot")
    cmd = StoreCommand(ref, LiteralQuery(42))
    thunk = cmd.compile(0, (_make_thunk(None), _make_thunk(EMPTY)))
    with pytest.raises(ValueError, match="sentinel"):
        thunk(None)


def test_store_command_thunk_raises_on_invalid():
    ref = ItemRef("slot")
    cmd = StoreCommand(ref, LiteralQuery(42))
    thunk = cmd.compile(0, (_make_thunk(None), _make_thunk(INVALID)))
    with pytest.raises(ValueError, match="sentinel"):
        thunk(None)


# ---------------------------------------------------------------------------
# PrimitiveStoreCommand (#5 — v1 parity)
# ---------------------------------------------------------------------------


def test_primitive_store_command_is_command():
    assert issubclass(PrimitiveStoreCommand, Command)


def test_primitive_store_command_constructs_with_ref_and_value():
    ref = ItemRef("slot")
    cmd = PrimitiveStoreCommand(ref, LiteralQuery({"a": 1}))
    assert len(cmd.children) == 2


def test_primitive_store_command_mutates_slot_zero():
    mutates = PrimitiveStoreCommand.attributes.get("mutates")
    assert mutates is not None
    assert 0 in mutates.value


def test_primitive_store_command_thunk_raises_on_empty():
    ref = ItemRef("slot")
    cmd = PrimitiveStoreCommand(ref, LiteralQuery(42))
    thunk = cmd.compile(0, (_make_thunk(None), _make_thunk(EMPTY)))
    with pytest.raises(ValueError, match="sentinel"):
        thunk(None)


def test_primitive_store_command_thunk_raises_on_invalid():
    ref = ItemRef("slot")
    cmd = PrimitiveStoreCommand(ref, LiteralQuery(42))
    thunk = cmd.compile(0, (_make_thunk(None), _make_thunk(INVALID)))
    with pytest.raises(ValueError, match="sentinel"):
        thunk(None)
