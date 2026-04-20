"""Tests for distributed preset - Ray actors with shared storage."""

from __future__ import annotations

import pytest
from conftest import TestShape, distributed

import nu_virtuals as ebv
from composables import Runtime
from nu import ForRange, Parallel, Print, Seq
from nu_distributed import NavigatorSpec, RocksDBStorageSpec, Teleport


def _store_and_read_flow() -> object:
    """Write on worker 0, read on worker 1 (shared storage)."""
    return Seq(
        Teleport(
            ebv.Transaction(
                TestShape.price.store(42.0),
                TestShape.quantity.store(100),
            ),
            worker=0,
        ),
        Teleport(
            ebv.Snapshot(
                Print("[verify] price", TestShape.price),
                Print("[verify] quantity", TestShape.quantity),
            ),
            worker=1,
        ),
    )


@pytest.mark.asyncio
async def test_distributed_basic(db_path):
    """Two Ray workers, shared RocksDB, sequential write then read."""
    async with Runtime() as rt:
        ctx = await distributed(
            rt,
            NavigatorSpec(storage_resource=RocksDBStorageSpec(path=db_path)),
            workers=2,
        )
        await _store_and_read_flow().execute(ctx)


@pytest.mark.asyncio
async def test_distributed_parallel(db_path):
    """Parallel writes across workers."""
    flow = Seq(
        # Init on worker 0
        Teleport(
            ebv.Transaction(
                TestShape.price.store(0),
                TestShape.quantity.store(0),
            ),
            worker=0,
        ),
        # Parallel writes
        Parallel(
            Teleport(
                ebv.Transaction(TestShape.price.store(99.5)),
                worker=0,
            ),
            Teleport(
                ebv.Transaction(TestShape.quantity.store(500)),
                worker=1,
            ),
        ),
    )
    async with Runtime() as rt:
        ctx = await distributed(
            rt,
            NavigatorSpec(storage_resource=RocksDBStorageSpec(path=db_path)),
            workers=2,
        )
        await flow.execute(ctx)


@pytest.mark.asyncio
async def test_distributed_many_workers(db_path):
    """Four workers, sequential writes to shared storage."""
    flow = Seq(
        Teleport(
            ebv.Transaction(
                TestShape.price.store(0),
                TestShape.quantity.store(0),
            ),
            worker=0,
        ),
        # Sequential to avoid RocksDB lock contention on same key
        *(
            Teleport(
                ebv.Transaction(TestShape.price.store(float(i * 10))),
                worker=i,
            )
            for i in range(4)
        ),
    )
    async with Runtime() as rt:
        ctx = await distributed(
            rt,
            NavigatorSpec(storage_resource=RocksDBStorageSpec(path=db_path)),
            workers=4,
        )
        await flow.execute(ctx)


@pytest.mark.asyncio
async def test_distributed_forrange(db_path):
    """ForRange loop on a Ray worker."""
    flow = Seq(
        Teleport(
            ebv.Transaction(TestShape.price.store(0)),
            worker=0,
        ),
        Teleport(
            ForRange(
                0,
                10,
                ebv.Transaction(TestShape.price.store(42.0)),
            ),
            worker=0,
        ),
    )
    async with Runtime() as rt:
        ctx = await distributed(
            rt,
            NavigatorSpec(storage_resource=RocksDBStorageSpec(path=db_path)),
            workers=1,
        )
        await flow.execute(ctx)
