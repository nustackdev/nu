"""Runs that overlap on one LMDB path in one process share its env.

LMDB allows one open env per path per process; every test here would hang or
raise "already open" without the shared env, so each runs under a timeout.
"""

from __future__ import annotations

import asyncio
import threading

import pytest

import nu
import nustd
from nu.forms import Dict
from nustd.blob import LMDBBackend, StoreRef
from nustd.blob.backends import lmdb as lmdb_backend


pytestmark = pytest.mark.timeout(60)


Media = StoreRef("media")
Pics = StoreRef("pics")


@pytest.fixture(autouse=True)
def _no_env_left_open():
    yield
    assert lmdb_backend._SHARED == {}


def test_gathered_async_runs_on_one_path(tmp_path):
    path = tmp_path / "env"

    async def main():
        runs = (
            nu.arun(nu.With(nustd.blob.lmdb(Media, path), body=Media.put(b"x"))) for _ in range(6)
        )
        return await asyncio.gather(*runs)

    ids = [out[0] for out in asyncio.run(main())]
    assert len(set(ids)) == 6
    for bid in ids:
        assert nu.run(nu.With(nustd.blob.lmdb(Media, path), body=Media.has(bid)))[0] is True


def test_second_run_while_a_root_stream_is_held(tmp_path):
    path = tmp_path / "env"
    data = b"abcdef" * 1000
    bid = nu.run(nu.With(nustd.blob.lmdb(Media, path), body=Media.put(data)))[0]
    pieces = nu.run(nu.With(nustd.blob.lmdb(Media, path), body=Media.open(bid, step=1000)))[0]
    first = next(pieces)
    other = nu.run(nu.With(nustd.blob.lmdb(Media, path), body=Media.put(b"other")))[0]
    assert nu.run(nu.With(nustd.blob.lmdb(Media, path), body=Media.get(other)))[0] == b"other"
    assert first + b"".join(pieces) == data


def test_two_stores_on_one_path_in_one_tree(tmp_path):
    path = tmp_path / "env"
    term = nu.With(
        nustd.blob.lmdb(Media, path),
        nustd.blob.lmdb(Pics, path),
        body=nu.let(
            Media.put(b"m"),
            lambda bid: Dict.of(bid=bid, via_pics=Pics.get(bid), in_pics=Pics.has(bid)),
        ),
    )
    out = nu.run(term)[0]
    assert out["via_pics"] == b"m"
    assert out["in_pics"] is True


def test_runs_from_threads_on_one_path(tmp_path):
    path = tmp_path / "env"
    ids: list[str] = []
    errors: list[BaseException] = []

    def work():
        try:
            for _ in range(5):
                ids.append(nu.run(nu.With(nustd.blob.lmdb(Media, path), body=Media.put(b"t")))[0])
        except BaseException as error:
            errors.append(error)

    threads = [threading.Thread(target=work) for _ in range(8)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join(30)
    assert not any(thread.is_alive() for thread in threads), "a run hung"
    assert errors == []
    assert len(set(ids)) == 40


def test_backends_share_the_env_and_the_last_close_closes_it(tmp_path):
    a = LMDBBackend(tmp_path / "env")
    b = LMDBBackend(tmp_path / "env")
    a.open()
    b.open()
    assert a._env is b._env
    assert a._write_lock is b._write_lock
    info = a.put(b"shared")
    a.close()
    assert b.read(info.id) == b"shared"
    b.close()
    with pytest.raises(RuntimeError, match="not open"):
        b.read(info.id)


def test_open_twice_counts_once(tmp_path):
    backend = LMDBBackend(tmp_path / "env")
    backend.open()
    backend.open()
    backend.close()
    backend.close()


@pytest.mark.parametrize(
    "options",
    [
        {"map_size": 1 << 30},
        {"writemap": not lmdb_backend.DEFAULT_WRITEMAP},
        {"max_readers": 8},
    ],
)
def test_conflicting_options_raise(tmp_path, options):
    held = LMDBBackend(tmp_path / "env")
    held.open()
    try:
        with pytest.raises(ValueError, match="already open in this process"):
            LMDBBackend(tmp_path / "env", **options).open()
    finally:
        held.close()
