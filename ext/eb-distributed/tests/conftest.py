"""Shared fixtures for eb-distributed integration tests."""

import uuid
from pathlib import Path

import pytest

import eb_virtuals as ebv
from everybase.shape import Shape


# Shape defined at module level (not __main__) so it survives pickling across processes
class TestShape(Shape):
    price = ebv.FloatRef.slot()
    quantity = ebv.IntRef.slot()


@pytest.fixture
def sock(request):
    """Generate short unique socket path under /tmp (AF_UNIX path limit)."""
    uid = uuid.uuid4().hex[:8]
    prefix = request.node.name[:10]
    path = f"/tmp/.eb-test-{prefix}-{uid}"
    yield path
    # Cleanup
    for suffix in ["", "0", "1", "-state", "-w0", "-w1"]:
        p = path + suffix
        if Path(p).exists():
            Path(p).unlink()
