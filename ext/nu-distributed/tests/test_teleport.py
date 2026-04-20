"""Tests for Teleport span with various tag types."""

from __future__ import annotations

import pytest
from conftest import TestShape, local

import nu_virtuals as ebv
from composables import Runtime
from nu_distributed import NavigatorSpec, Teleport


@pytest.mark.asyncio
async def test_teleport_int_tag():
    """Standard integer index tag."""
    flow = Teleport(
        ebv.Transaction(TestShape.price.store(10.0)),
        worker=0,
    )
    async with Runtime() as rt:
        ctx = await local(rt, NavigatorSpec(), workers=2)
        await flow.execute(ctx)


@pytest.mark.asyncio
async def test_teleport_multiple_children():
    """Multiple children wrapped in Seq automatically."""
    flow = Teleport(
        ebv.Transaction(TestShape.price.store(1.0)),
        ebv.Transaction(TestShape.quantity.store(2)),
        worker=0,
    )
    async with Runtime() as rt:
        ctx = await local(rt, NavigatorSpec(), workers=1)
        await flow.execute(ctx)


@pytest.mark.asyncio
async def test_teleport_string_tag():
    """String tag for capability-based routing."""
    from nu_distributed import Worker

    flow = Teleport(
        ebv.Transaction(TestShape.price.store(42.0)),
        worker="gpu",
    )
    async with Runtime() as rt:
        ctx = await local(rt, NavigatorSpec(), workers=1)
        # Rebind worker with string tag
        worker = ctx.get(Worker, 0)
        ctx = ctx.bind(Worker, worker, "gpu")
        await flow.execute(ctx)


@pytest.mark.asyncio
async def test_teleport_tuple_tag():
    """Tuple tag for machine+index routing."""
    from nu_distributed import Worker

    flow = Teleport(
        ebv.Transaction(TestShape.price.store(42.0)),
        worker=("red", 0),
    )
    async with Runtime() as rt:
        ctx = await local(rt, NavigatorSpec(), workers=1)
        # Rebind worker with tuple tag
        worker = ctx.get(Worker, 0)
        ctx = ctx.bind(Worker, worker, ("red", 0))
        await flow.execute(ctx)


@pytest.mark.asyncio
async def test_teleport_repr():
    """Verify repr shows tag."""
    t = Teleport(ebv.Transaction(TestShape.price.store(1.0)), worker=0)
    assert repr(t) == "Teleport(worker=0)"

    t2 = Teleport(ebv.Transaction(TestShape.price.store(1.0)), worker="gpu")
    assert repr(t2) == "Teleport(worker='gpu')"

    t3 = Teleport(ebv.Transaction(TestShape.price.store(1.0)), worker=("red", 0))
    assert repr(t3) == "Teleport(worker=('red', 0))"
