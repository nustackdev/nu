"""Media.open is a real stream: a pull reads one piece and nothing runs ahead.

A counting backend records every piece its ``stream`` hands out, and the
thread it was read on. Pulling the first piece of a ten piece blob must read
exactly one, under both runners, and the async runner must read it off the
event loop's thread.
"""

from __future__ import annotations

import asyncio
import threading

import pytest
from _support.blob_workers import BUCKET

import nu
from nustd.blob import BlobFabric, FilesBackend, LMDBBackend, S3Backend, StoreRef


STEP = 1000
DATA = bytes(range(250)) * 40  # 10000 bytes: ten pieces of STEP


Media = StoreRef("media")


class Reads:
    """Every piece a counting backend handed out: (size, thread id)."""

    log: list[tuple[int, int]] = []  # noqa: RUF012


def _counted(pieces):
    for piece in pieces:
        Reads.log.append((len(piece), threading.get_ident()))
        yield piece


class CountingFiles(FilesBackend):
    def stream(self, blob_id, start=0, end=None, *, step=STEP):
        return _counted(super().stream(blob_id, start, end, step=step))


class CountingLMDB(LMDBBackend):
    def stream(self, blob_id, start=0, end=None, *, step=STEP):
        return _counted(super().stream(blob_id, start, end, step=step))


class CountingS3(S3Backend):
    def stream(self, blob_id, start=0, end=None, *, step=STEP):
        return _counted(super().stream(blob_id, start, end, step=step))


@pytest.fixture
def counting(kind, tmp_path):
    """The Media binding over a counting backend, with one ten piece blob in it."""
    if kind == "s3":
        spec = {"backend": CountingS3, "options": {"bucket": BUCKET, "prefix": "s/"}}
    elif kind == "lmdb":
        spec = {"backend": CountingLMDB, "options": {"path": str(tmp_path / "s")}}
    else:
        spec = {"backend": CountingFiles, "options": {"root": str(tmp_path / "s")}}

    def tree(body):
        return nu.Provide(BlobFabric, kwargs=spec, body=body, tag=Media.name)

    bid = nu.run(tree(Media.put(DATA)))[0]
    Reads.log.clear()
    return tree, bid


def test_sync_pull_of_one_piece_reads_one_piece(counting):
    tree, bid = counting
    first = nu.run(tree(nu.First(Media.open(bid, step=STEP))))[0]
    assert first == DATA[:STEP]
    assert len(Reads.log) == 1


def test_async_pull_of_one_piece_reads_one_piece_off_the_loop(counting):
    tree, bid = counting
    loop_thread = []

    async def main():
        loop_thread.append(threading.get_ident())
        return (await nu.arun(tree(nu.First(Media.open(bid, step=STEP)))))[0]

    first = asyncio.run(main())
    assert first == DATA[:STEP]
    assert len(Reads.log) == 1
    assert Reads.log[0][1] != loop_thread[0]


def test_first_of_a_range_reads_one_piece(counting):
    tree, bid = counting
    first = nu.run(tree(nu.First(Media.open(bid, 4500, None, STEP))))[0]
    assert first == DATA[4500:5500]
    assert len(Reads.log) == 1


@pytest.mark.parametrize("mode", ["sync", "async"])
def test_full_drain_reads_each_piece_once(counting, mode):
    tree, bid = counting
    term = tree(nu.Collect(Media.open(bid, step=STEP)))
    pieces = nu.run(term)[0] if mode == "sync" else asyncio.run(nu.arun(term))[0]
    assert b"".join(pieces) == DATA
    assert [size for size, _ in Reads.log] == [STEP] * 10


def test_sync_root_stream_is_a_generator_pulled_by_the_caller(counting):
    tree, bid = counting
    pieces = nu.run(tree(Media.open(bid, step=STEP)))[0]
    assert Reads.log == []
    assert next(pieces) == DATA[:STEP]
    assert len(Reads.log) == 1
    assert b"".join(pieces) == DATA[STEP:]
    assert len(Reads.log) == 10


def test_async_root_stream_is_an_async_generator_pulled_by_the_caller(counting):
    tree, bid = counting

    async def main():
        pieces = (await nu.arun(tree(Media.open(bid, step=STEP))))[0]
        assert Reads.log == []
        assert await pieces.__anext__() == DATA[:STEP]
        assert len(Reads.log) == 1
        rest = [piece async for piece in pieces]
        assert b"".join(rest) == DATA[STEP:]
        assert len(Reads.log) == 10

    asyncio.run(main())
