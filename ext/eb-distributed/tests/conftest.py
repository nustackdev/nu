"""Shared fixtures and test utilities for eb-distributed tests."""

from __future__ import annotations

import shutil
import tempfile

import pytest
import ray

import eb_virtuals as ebv
from everybase.shape import Shape


class TestShape(Shape):
    """Test shape with price and quantity fields."""

    price = ebv.FloatRef.slot()
    quantity = ebv.IntRef.slot()


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
