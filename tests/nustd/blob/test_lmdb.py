"""What only the LMDB backend promises: its size cap, its env, its map."""

from __future__ import annotations

import sys

import pytest

from nustd.blob import BlobNotFound, BlobTooLarge, LMDBBackend
from nustd.blob._base import new_id
from nustd.blob.backends.lmdb import DEFAULT_MAP_SIZE, DEFAULT_WRITEMAP, MAX_VALUE


@pytest.fixture
def env(tmp_path):
    backend = LMDBBackend(tmp_path / "env")
    backend.open()
    yield backend
    backend.close()


def test_value_over_the_cap_is_refused_before_writing(env, tmp_path):
    # A sparse file: 4 GiB of size, no disk behind it.
    source = tmp_path / "huge.bin"
    with source.open("wb") as file:
        file.truncate(MAX_VALUE + 1)
    bid = new_id()
    with pytest.raises(BlobTooLarge):
        env.put(source, blob_id=bid)
    assert not env.exists(bid)
    assert list(env._spool_dir.iterdir()) == []


def test_buffer_over_the_cap_is_refused(env, monkeypatch):
    monkeypatch.setattr(env, "max_size", 10)
    with pytest.raises(BlobTooLarge):
        env.put(b"x" * 11)


def test_default_map_is_sparse(env):
    data = env.path / "data.mdb"
    env.put(b"x" * 100_000)
    assert env.map_size == DEFAULT_MAP_SIZE == 1 << 40
    assert data.stat().st_blocks * 512 < 64 << 20


def test_writemap_default_follows_the_platform():
    # macOS pays per GiB of map on every writemap commit: 14 s a put at 1 TiB.
    assert DEFAULT_WRITEMAP is (sys.platform != "darwin")
    assert LMDBBackend("unused").writemap is DEFAULT_WRITEMAP


@pytest.mark.parametrize("writemap", [False, True])
def test_either_writemap_puts_and_reads(tmp_path, writemap):
    # A small map keeps the writemap run fast on macOS too.
    backend = LMDBBackend(tmp_path / "env", map_size=1 << 30, writemap=writemap)
    backend.open()
    info = backend.put(iter([b"a", b"b"]))
    assert backend.read(info.id) == b"ab"
    backend.close()


def test_data_and_meta_in_one_txn(env):
    info = env.put(b"abc", mime="m")
    with env._env.begin() as txn:
        assert txn.get(info.id.encode(), db=env._data) == b"abc"
        assert txn.get(info.id.encode(), db=env._meta) is not None
    env.delete(info.id)
    with env._env.begin() as txn:
        assert txn.get(info.id.encode(), db=env._data) is None
        assert txn.get(info.id.encode(), db=env._meta) is None


def active_readers(backend):
    rows = backend._env.readers().splitlines()[1:]
    return [row for row in rows if row.split()[-1] != "-"]


def test_stream_holds_no_reader_between_pulls(env):
    info = env.put(b"x" * 1000)
    pieces = env.stream(info.id, step=100)
    assert next(pieces) == b"x" * 100
    assert active_readers(env) == []
    assert b"".join(pieces) == b"x" * 900


def test_closed_env_refuses(tmp_path):
    backend = LMDBBackend(tmp_path / "env")
    with pytest.raises(RuntimeError, match="not open"):
        backend.read(new_id())
    backend.open()
    backend.close()
    with pytest.raises(RuntimeError, match="not open"):
        backend.put(b"x")


def test_reopen_sees_blobs(tmp_path):
    first = LMDBBackend(tmp_path / "env")
    first.open()
    info = first.put(b"kept", name="k")
    first.close()
    second = LMDBBackend(tmp_path / "env")
    second.open()
    assert second.info(info.id) == info
    second.close()


@pytest.mark.parametrize("size", [300, 1000, 5000], ids=["shorter", "same", "longer"])
def test_stream_refuses_a_blob_replaced_mid_stream(env, size):
    bid = new_id()
    env.put(b"a" * 1000, blob_id=bid)
    pieces = env.stream(bid, step=100)
    assert next(pieces) == b"a" * 100
    env.delete(bid)
    env.put(b"b" * size, blob_id=bid)
    with pytest.raises(BlobNotFound):
        next(pieces)


def test_stream_raises_on_a_blob_deleted_mid_stream(env):
    info = env.put(b"a" * 1000)
    pieces = env.stream(info.id, step=100)
    next(pieces)
    env.delete(info.id)
    with pytest.raises(BlobNotFound):
        next(pieces)
