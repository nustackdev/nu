"""Two spawned processes write and read one store at once, per backend."""

from __future__ import annotations

import multiprocessing

import pytest
from _support.blob_workers import CONTESTED, LOCAL_KINDS, blob_id, content, make, writer


@pytest.fixture(params=LOCAL_KINDS)
def kind(request):
    # Local backends only: a spawned child cannot reach the moto S3 inside
    # this process, and many processes on one bucket is S3's own job.
    return request.param


COUNT = 25


@pytest.mark.parametrize("precheck", [True, False], ids=["precheck", "store-guard"])
def test_two_processes_share_a_store(kind, store_path, precheck):
    setup = make(kind, store_path)
    setup.open()  # created once up front, as a host would
    setup.close()
    ctx = multiprocessing.get_context("spawn")
    barrier = ctx.Barrier(2)
    out = ctx.Queue()
    children = [
        ctx.Process(
            target=writer,
            args=(kind, str(store_path), me, 1 - me, COUNT, barrier, out, precheck),
        )
        for me in (0, 1)
    ]
    for child in children:
        child.start()
    results = sorted(out.get(timeout=60) for _ in children)
    for child in children:
        child.join(timeout=30)
        assert child.exitcode == 0

    assert [seen for _, _, seen in results] == [COUNT, COUNT]
    assert sum(won for _, won, _ in results) == 1  # write-once across processes

    backend = make(kind, store_path)
    backend.open()
    try:
        for worker in (0, 1):
            for index in range(COUNT):
                assert backend.read(blob_id(worker, index)) == content(worker, index)
        assert backend.read(CONTESTED) in (content(0, 0), content(1, 0))
    finally:
        backend.close()
