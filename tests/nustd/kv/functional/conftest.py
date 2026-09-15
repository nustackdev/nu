"""Functional test configuration for virtuals tests (InMemory backend)."""

from collections.abc import Generator

import pytest

from nu import Context
from virtuals import Navigator
from virtuals.tkv.storage import SnapshotProtocol, StorageProtocol, TransactionProtocol


def pytest_configure(config: pytest.Config) -> None:
    """Register storage-backend markers (root config uses --strict-markers)."""
    for backend in ("inmemory", "rocksdb", "text", "lmdb"):
        config.addinivalue_line("markers", f"{backend}: storage backend parametrization")


# ============================================================================
# Backend Parametrization
# ============================================================================


@pytest.fixture(
    params=[
        pytest.param("inmemory", marks=pytest.mark.inmemory),
    ],
    scope="session",
)
def backend_type(request: pytest.FixtureRequest) -> str:
    """Storage backend type for parametrization (InMemory only here)."""
    return request.param


@pytest.fixture(scope="session")
def codec(backend_type: str):
    """Codec matched to backend type."""
    from virtuals.codecs import BinaryCodec

    return BinaryCodec()


# ============================================================================
# Storage Backend
# ============================================================================


@pytest.fixture
def storage(codec, backend_type: str) -> Generator[StorageProtocol, None, None]:
    """In-memory storage backend (function-scoped for test isolation)."""
    from virtuals.storages.mem import InMemoryStorage

    storage = InMemoryStorage(codec=codec)
    with storage:
        yield storage  # type: ignore[misc]


@pytest.fixture
def tx(storage: StorageProtocol) -> Generator[TransactionProtocol, None, None]:
    """Read-write transaction context."""
    with storage.transaction() as tx:
        yield tx


@pytest.fixture
def snapshot(storage: StorageProtocol) -> Generator[SnapshotProtocol, None, None]:
    """Read-only snapshot context."""
    with storage.snapshot() as snap:
        yield snap


@pytest.fixture
def nav(storage: StorageProtocol) -> Navigator:
    """Navigator instance for tests."""
    return Navigator(storage)


@pytest.fixture
def ctx(tx: TransactionProtocol, nav: Navigator) -> Context:
    """Context bundling Navigator and transaction (v2 type-first bind)."""
    return Context().bind(Navigator, nav).bind(TransactionProtocol, tx)
