"""Shared fixtures and test utilities for eb-distributed tests."""

from __future__ import annotations

import shutil
import socket
import tempfile

import pytest
import ray
from composables.spec import SpecBuilder

import nu_virtuals as ebv
from nu_distributed import (
    ContextSpec,
    InvisiblesClientSpec,
    InvisiblesServerSpec,
    NavigatorSpec,
    RayActorSpec,
    RayWorkerSpec,
    Worker,
    WorkerSpec,
)
from nu import Context
from nu.shapes import Shape


class TestShape(Shape):
    """Test shape with price and quantity fields."""

    price = ebv.FloatRef.slot()
    quantity = ebv.IntRef.slot()


async def local(runtime, nav_spec: NavigatorSpec, *, workers: int = 2) -> Context:
    """Test helper: local in-process workers."""
    ctx = Context()
    for i in range(workers):
        worker = await runtime.create(
            WorkerSpec(name=f"worker-{i}", context=ContextSpec(storage=nav_spec))
        )
        ctx = ctx.bind(Worker, worker, i)
    return ctx


async def distributed(runtime, nav_spec: NavigatorSpec, *, workers: int = 2) -> Context:
    """Test helper: Ray actors with shared storage via invisibles."""
    port = _find_free_port()
    host = ray.util.get_node_ip_address()
    address = f"{host}:{port}"

    await runtime.create(
        RayActorSpec(
            name="storage-service",
            inner_spec=InvisiblesServerSpec(
                transport="tcp",
                address=address,
                executor="threaded",
                root_service=nav_spec,
            ),
            actor_name="eb-storage",
        )
    )

    worker_nav = (
        SpecBuilder(nav_spec)
        .as_proxy(InvisiblesClientSpec(transport="tcp", address=address))
        .build()
    )

    ctx = Context()
    for i in range(workers):
        worker = await runtime.create(
            RayWorkerSpec(
                name=f"worker-{i}",
                inner_spec=WorkerSpec(context=ContextSpec(storage=worker_nav)),
                actor_name=f"eb-worker-{i}",
            )
        )
        ctx = ctx.bind(Worker, worker, i)
    return ctx


def _find_free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("", 0))
        return s.getsockname()[1]


@pytest.fixture(scope="session", autouse=True)
def ray_session():
    """Start Ray once for the entire test session."""
    ray.init(num_cpus=4, ignore_reinit_error=True)
    yield
    ray.shutdown()


@pytest.fixture
def db_path():
    """Temporary RocksDB directory, cleaned up after test."""
    path = tempfile.mkdtemp(prefix="eb-test-rocksdb-")
    yield path
    shutil.rmtree(path, ignore_errors=True)
