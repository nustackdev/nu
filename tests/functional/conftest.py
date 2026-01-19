"""Functional test configuration and shared fixtures."""

import pathlib
from collections.abc import Generator

import pytest

from pv.view import View
from pv.storage import SnapshotProtocol, StorageProtocol, TransactionProtocol
from everyterm.term import Context


# ============================================================================
# Backend Parametrization (future-proof)
# ============================================================================


@pytest.fixture(
    params=[
        pytest.param("rocksdb", marks=pytest.mark.rocksdb),
        # pytest.param("inmemory", marks=pytest.mark.inmemory),
        # pytest.param("text", marks=pytest.mark.text), # TODO: fix locking issues, enable testing
        # Future backends (currently commented out in codebase):
        # pytest.param("lmdb", marks=[pytest.mark.lmdb, pytest.mark.skip("not implemented")]),
    ],
    scope="session",
)
def backend_type(request: pytest.FixtureRequest) -> str:
    """Storage backend type for parametrization.

    Currently active: RocksDB, Text (debug storage), and InMemory (fast ephemeral).
    LMDB implementation is commented out in the codebase.
    """
    return request.param


# ============================================================================
# Codec Parametrization
# ============================================================================


@pytest.fixture(scope="session")
def codec(backend_type: str):
    """Codec matched to backend type."""
    from everybase.adapters.codecs import BinaryCodec, TextCodec

    if backend_type == "rocksdb":
        return BinaryCodec()
    elif backend_type == "text":
        return TextCodec()
    elif backend_type == "inmemory":
        return BinaryCodec()
    else:
        raise ValueError(f"No codec for backend: {backend_type}")


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
        from everybase.adapters.storages.rocksdb import RocksDBStorage

        storage = RocksDBStorage(path=tmp_path / "test_db", codec=codec)
    elif backend_type == "text":
        from everybase.adapters.storages.textdb import TextStorage

        storage = TextStorage(path=tmp_path / "test_db", codec=codec, log_operations=True)
    elif backend_type == "inmemory":
        from everybase.adapters.storages.inmemdb import InMemoryStorage

        storage = InMemoryStorage(codec=codec)
    else:
        raise ValueError(f"Backend not implemented: {backend_type}")

    with storage:
        yield storage  # type: ignore


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


# ============================================================================
# Root View Fixture
# ============================================================================


@pytest.fixture
def root_view(tx: TransactionProtocol) -> View:
    """Root DictView for esstd tests.

    Creates the root container at "/" with DictView, providing a mapping
    interface to the entire tree. All other views should navigate from this root.

    Dependency chain: codec → storage → tx → root_view
    """
    from everybase.view import DictView

    return DictView.open_root(ctx=tx)


# ============================================================================
# Context Fixture
# ============================================================================


@pytest.fixture
def ctx(root_view: View, tx: TransactionProtocol) -> Context:
    """Context bundling root view and transaction.

    Used by shapes layer for executing operations and commands.

    Dependency chain: codec → storage → tx → root_view → ctx
    """
    return Context.create(root_view=root_view, storage_context=tx)
