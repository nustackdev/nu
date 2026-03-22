"""Tests for local preset - in-process workers, no Ray."""

from __future__ import annotations

import pytest
from composables import Runtime

import eb_virtuals as ebv
from eb_distributed import NavigatorSpec, Teleport, local
from eb_distributed.testing import TestShape
from everybase.abc import Parallel, Seq


def _make_flow() -> object:
    """Create a fresh flow for each test (avoids stale proxy refs)."""
    return Seq(
        Teleport(
            ebv.Transaction(
                TestShape.price.store(42.0),
                TestShape.quantity.store(10),
            ),
            worker=0,
        ),
        Teleport(
            ebv.Transaction(
                TestShape.price.store(99.5),
                TestShape.quantity.store(20),
            ),
            worker=1,
        ),
    )


@pytest.mark.asyncio
async def test_local_basic():
    """Two workers, sequential writes."""
    async with Runtime() as rt:
        ctx = await local(rt, NavigatorSpec(), workers=2)
        await _make_flow().execute(ctx)


@pytest.mark.asyncio
async def test_local_parallel():
    """Parallel execution across workers."""
    flow = Parallel(
        Teleport(
            ebv.Transaction(TestShape.price.store(1.0)),
            worker=0,
        ),
        Teleport(
            ebv.Transaction(TestShape.quantity.store(2)),
            worker=1,
        ),
    )
    async with Runtime() as rt:
        ctx = await local(rt, NavigatorSpec(), workers=2)
        await flow.execute(ctx)


@pytest.mark.asyncio
async def test_local_single_worker():
    """Single worker setup."""
    flow = Teleport(
        ebv.Transaction(TestShape.price.store(55.0)),
        worker=0,
    )
    async with Runtime() as rt:
        ctx = await local(rt, NavigatorSpec(), workers=1)
        await flow.execute(ctx)
