"""Every Redis-notified stack defaults to the ``"nu"`` channel prefix.

The RocksDB pair used to default to ``"__every__"`` while every other preset
and the publisher and observer fabrics said ``"nu"``, so two stacks left on
their defaults never heard each other.
"""

from __future__ import annotations

import inspect

import pytest

from nustd.kv import presets
from nustd.kv.fabrics.observer import RedisObserver
from nustd.kv.fabrics.publisher import RedisPublisher


def _default(fn: object) -> object:
    return inspect.signature(fn).parameters["channel_prefix"].default


@pytest.mark.parametrize(
    "fn",
    [
        presets.rocksdb_storage_redis,
        presets.rocksdb_navigator_redis,
        presets.lmdb_navigator_redis,
        presets.sqlite_navigator_redis,
        presets.redis_observer,
        RedisPublisher,
        RedisObserver,
    ],
)
def test_the_default_channel_prefix_is_nu(fn) -> None:
    assert _default(fn) == "nu"
