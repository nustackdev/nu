"""Functional test configuration and shared fixtures."""

import pathlib
from collections.abc import Generator

import pytest

from redwood.storage import SnapshotProtocol, StorageProtocol, TransactionProtocol


# ============================================================================
# Backend Parametrization (future-proof)
# ============================================================================


@pytest.fixture(
    params=[
        pytest.param("rocksdb", marks=pytest.mark.rocksdb),
        # Future backends (currently commented out in codebase):
        # pytest.param("lmdb", marks=[pytest.mark.lmdb, pytest.mark.skip("not implemented")]),
        # pytest.param("inmemory", marks=[pytest.mark.inmemory, pytest.mark.skip("not implemented")]),
    ],
    scope="session",
)
def backend_type(request: pytest.FixtureRequest) -> str:
    """Storage backend type for parametrization.

    Currently only RocksDB is active. LMDB and InMemory implementations
    are commented out in the codebase.
    """
    return request.param


# ============================================================================
# Codec Parametrization
# ============================================================================


@pytest.fixture(
    params=["binary"],  # Start with binary only
    scope="session",
)
def codec(request: pytest.FixtureRequest):
    """Codec for key/value encoding.

    Currently parametrized with binary only. Can expand to test
    multiple codecs if needed: ["binary", "text", "noop"]
    """
    from rwstd.storage.codecs import BinaryCodec, NoOpCodec, TextCodec

    codecs = {
        "binary": BinaryCodec,
        "text": TextCodec,
        "noop": NoOpCodec,
    }
    return codecs[request.param]()


# ============================================================================
# Storage Backend
# ============================================================================


@pytest.fixture
def storage(
    tmp_path: pathlib.Path,
    codec,
    backend_type: str,
) -> Generator[StorageProtocol, None, None]:
    """Storage backend instance (function-scoped for test isolation).

    Dependency chain: codec (session) → backend_type (session) → storage (function)

    Uses tmp_path for ephemeral test databases. Each test gets a clean storage instance.
    """
    if backend_type == "rocksdb":
        from rwstd.storage.storage_rocksdb import RocksDBStorage

        storage = RocksDBStorage(path=tmp_path / "test_db", codec=codec)
    else:
        raise ValueError(f"Backend not implemented: {backend_type}")

    with storage:
        yield storage


# ============================================================================
# Storage Contexts
# ============================================================================


@pytest.fixture
def tx(storage: StorageProtocol) -> Generator[TransactionProtocol, None, None]:
    """Read-write transaction context.

    Auto-commits on successful completion, rolls back on exception.
    """
    with storage.transaction() as tx:
        yield tx


@pytest.fixture
def snapshot(storage: StorageProtocol) -> Generator[SnapshotProtocol, None, None]:
    """Read-only snapshot context.

    Useful for testing isolation and concurrent read scenarios.
    """
    with storage.snapshot() as snap:
        yield snap
