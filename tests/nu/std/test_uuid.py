"""Functional tests for ``nu.std.uuid`` - drive the Forms through the engine.

Covers the three modeling paths: constructors (factory atoms), attribute reads
(core ``GetAttr``), and comparison (core atoms), sync and async.
"""

from __future__ import annotations

import asyncio
import uuid as pyuuid

from nu.lang.helpers import arun, run
from nu.std.uuid import UUID, uuid4, uuid5


NS = "12345678-1234-5678-1234-567812345678"


def test_from_str_roundtrip() -> None:
    value, _ = run(UUID.from_str(NS))
    assert value == pyuuid.UUID(NS)


def test_from_bytes() -> None:
    value, _ = run(UUID.from_bytes(pyuuid.UUID(NS).bytes))
    assert value == pyuuid.UUID(NS)


def test_from_int() -> None:
    value, _ = run(UUID.from_int(pyuuid.UUID(NS).int))
    assert value == pyuuid.UUID(NS)


def test_version_accessor() -> None:
    # a v5 UUID has a real version; accessor reuses core GetAttr
    value, _ = run(uuid5(UUID.from_str(NS), "nu").version())
    assert value == 5


def test_hex_conversion() -> None:
    value, _ = run(UUID.from_str(NS).hex())
    assert value == pyuuid.UUID(NS).hex


def test_eq_comparison() -> None:
    value, _ = run(UUID.from_str(NS).eq(UUID.from_str(NS)))
    assert value is True


def test_uuid5_is_deterministic() -> None:
    value, _ = run(uuid5(UUID.from_str(NS), "nu"))
    assert value == pyuuid.uuid5(pyuuid.UUID(NS), "nu")


def test_uuid4_is_a_version_4_uuid() -> None:
    value, _ = run(uuid4())
    assert isinstance(value, pyuuid.UUID)
    assert value.version == 4


def test_runs_on_async_path() -> None:
    value, _ = asyncio.run(arun(UUID.from_str(NS).hex()))
    assert value == pyuuid.UUID(NS).hex
