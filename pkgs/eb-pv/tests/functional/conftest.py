"""Functional test configuration for PV stdtype tests."""

import pathlib
from collections.abc import Generator

import pytest
from pv.view import View
from tkv.tkv.storage import SnapshotProtocol, StorageProtocol, TransactionProtocol

from eb_pv import (
    PVComplexRef,
    PVDateRef,
    PVDatetimeRef,
    PVDecimalRef,
    PVFractionRef,
    PVPathRef,
    PVPercentageRef,
    PVTimedeltaRef,
    PVTimeRef,
    PVTimezoneRef,
    PVUUIDRef,
)
from eb_pv import (
    Shape as PVShape,
)
from everybase import Context


# ============================================================================
# Backend Parametrization (future-proof)
# ============================================================================


@pytest.fixture(
    params=[
        # pytest.param("rocksdb", marks=pytest.mark.rocksdb),
        pytest.param("inmemory", marks=pytest.mark.inmemory),
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
    from tkv.codecs import BinaryCodec, TextCodec

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
        from tkv.storages.rocksdb import RocksDBStorage

        storage = RocksDBStorage(path=tmp_path / "test_db", codec=codec)
    elif backend_type == "text":
        from tkv.storages.textdb import TextStorage

        storage = TextStorage(path=tmp_path / "test_db", codec=codec, log_operations=True)
    elif backend_type == "inmemory":
        from tkv.storages.mem import InMemoryStorage

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
    from eb_pv.views import DictView

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
    return Context().with_handle(View, root_view).with_handle(TransactionProtocol, tx)


# ============================================================================
# SHAPE FIXTURES
# ============================================================================


@pytest.fixture
def date_shape() -> type[PVShape]:
    """Shape with DateSlot."""

    class Event(PVShape):
        event_date = PVDateRef.slot()
        start_date = PVDateRef.slot()
        end_date = PVDateRef.slot()

    return Event


@pytest.fixture
def datetime_shape() -> type[PVShape]:
    """Shape with DatetimeSlot."""

    class Event(PVShape):
        created_at = PVDatetimeRef.slot()
        updated_at = PVDatetimeRef.slot()
        scheduled_at = PVDatetimeRef.slot()

    return Event


@pytest.fixture
def decimal_shape() -> type[PVShape]:
    """Shape with DecimalSlot."""

    class Account(PVShape):
        balance = PVDecimalRef.slot()
        credit = PVDecimalRef.slot()
        debit = PVDecimalRef.slot()

    return Account


@pytest.fixture
def path_shape() -> type[PVShape]:
    """Shape with PathSlot."""

    class Config(PVShape):
        config_path = PVPathRef.slot()
        data_dir = PVPathRef.slot()
        log_file = PVPathRef.slot()

    return Config


@pytest.fixture
def time_shape() -> type[PVShape]:
    """Shape with TimeSlot."""

    class Schedule(PVShape):
        start_time = PVTimeRef.slot()
        end_time = PVTimeRef.slot()
        break_time = PVTimeRef.slot()

    return Schedule


@pytest.fixture
def timedelta_shape() -> type[PVShape]:
    """Shape with TimedeltaSlot."""

    class Task(PVShape):
        duration = PVTimedeltaRef.slot()
        timeout = PVTimedeltaRef.slot()
        interval = PVTimedeltaRef.slot()

    return Task


@pytest.fixture
def timezone_shape() -> type[PVShape]:
    """Shape with TimezoneSlot."""

    class Location(PVShape):
        local_tz = PVTimezoneRef.slot()
        display_tz = PVTimezoneRef.slot()

    return Location


@pytest.fixture
def uuid_shape() -> type[PVShape]:
    """Shape with UUIDSlot."""

    class Entity(PVShape):
        id = PVUUIDRef.slot()
        parent_id = PVUUIDRef.slot()
        correlation_id = PVUUIDRef.slot()

    return Entity


@pytest.fixture
def complex_shape() -> type[PVShape]:
    """Shape with ComplexSlot."""

    class Signal(PVShape):
        amplitude = PVComplexRef.slot()
        phase = PVComplexRef.slot()
        coefficient = PVComplexRef.slot()

    return Signal


@pytest.fixture
def fraction_shape() -> type[PVShape]:
    """Shape with FractionSlot."""

    class Ratio(PVShape):
        portion = PVFractionRef.slot()
        scale = PVFractionRef.slot()
        multiplier = PVFractionRef.slot()

    return Ratio


@pytest.fixture
def percentage_shape() -> type[PVShape]:
    """Shape with PercentageSlot."""

    class Metrics(PVShape):
        completion = PVPercentageRef.slot()
        discount = PVPercentageRef.slot()
        tax_rate = PVPercentageRef.slot()

    return Metrics
