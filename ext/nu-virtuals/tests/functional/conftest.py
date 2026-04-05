"""Functional test configuration for PV stdtype tests."""

import pathlib
from collections.abc import Generator

import pytest
from virtuals import Navigator
from virtuals.tkv.storage import SnapshotProtocol, StorageProtocol, TransactionProtocol

from nu_virtuals import (
    ComplexRef,
    DateRef,
    DatetimeRef,
    DecimalRef,
    FractionRef,
    PathRef,
    PercentageRef,
    TimedeltaRef,
    TimeRef,
    TimezoneRef,
    UUIDRef,
)
from nu import Context
from nu.shapes import Shape


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
    from virtuals.codecs import BinaryCodec, TextCodec

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
        from virtuals.storages.rocksdb import RocksDBStorage

        storage = RocksDBStorage(path=tmp_path / "test_db", codec=codec)
    elif backend_type == "text":
        from virtuals.storages.textdb import TextStorage

        storage = TextStorage(path=tmp_path / "test_db", codec=codec, log_operations=True)
    elif backend_type == "inmemory":
        from virtuals.storages.mem import InMemoryStorage

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
# Navigator Fixture
# ============================================================================


@pytest.fixture
def nav(storage: StorageProtocol) -> Navigator:
    """Navigator instance for tests."""
    return Navigator(storage)


# ============================================================================
# Context Fixture
# ============================================================================


@pytest.fixture
def ctx(tx: TransactionProtocol, nav: Navigator) -> Context:
    """Context bundling Navigator and transaction.

    Dependency chain: codec -> storage -> nav -> tx -> ctx
    """
    return Context().bind(nav, Navigator).bind(tx, TransactionProtocol)


# ============================================================================
# SHAPE FIXTURES
# ============================================================================


@pytest.fixture
def date_shape() -> type[Shape]:
    """Shape with DateSlot."""

    class Event(Shape):
        event_date = DateRef.slot()
        start_date = DateRef.slot()
        end_date = DateRef.slot()

    return Event


@pytest.fixture
def datetime_shape() -> type[Shape]:
    """Shape with DatetimeSlot."""

    class Event(Shape):
        created_at = DatetimeRef.slot()
        updated_at = DatetimeRef.slot()
        scheduled_at = DatetimeRef.slot()

    return Event


@pytest.fixture
def decimal_shape() -> type[Shape]:
    """Shape with DecimalSlot."""

    class Account(Shape):
        balance = DecimalRef.slot()
        credit = DecimalRef.slot()
        debit = DecimalRef.slot()

    return Account


@pytest.fixture
def path_shape() -> type[Shape]:
    """Shape with PathSlot."""

    class Config(Shape):
        config_path = PathRef.slot()
        data_dir = PathRef.slot()
        log_file = PathRef.slot()

    return Config


@pytest.fixture
def time_shape() -> type[Shape]:
    """Shape with TimeSlot."""

    class Schedule(Shape):
        start_time = TimeRef.slot()
        end_time = TimeRef.slot()
        break_time = TimeRef.slot()

    return Schedule


@pytest.fixture
def timedelta_shape() -> type[Shape]:
    """Shape with TimedeltaSlot."""

    class Task(Shape):
        duration = TimedeltaRef.slot()
        timeout = TimedeltaRef.slot()
        interval = TimedeltaRef.slot()

    return Task


@pytest.fixture
def timezone_shape() -> type[Shape]:
    """Shape with TimezoneSlot."""

    class Location(Shape):
        local_tz = TimezoneRef.slot()
        display_tz = TimezoneRef.slot()

    return Location


@pytest.fixture
def uuid_shape() -> type[Shape]:
    """Shape with UUIDSlot."""

    class Entity(Shape):
        id = UUIDRef.slot()
        parent_id = UUIDRef.slot()
        correlation_id = UUIDRef.slot()

    return Entity


@pytest.fixture
def complex_shape() -> type[Shape]:
    """Shape with ComplexSlot."""

    class Signal(Shape):
        amplitude = ComplexRef.slot()
        phase = ComplexRef.slot()
        coefficient = ComplexRef.slot()

    return Signal


@pytest.fixture
def fraction_shape() -> type[Shape]:
    """Shape with FractionSlot."""

    class Ratio(Shape):
        portion = FractionRef.slot()
        scale = FractionRef.slot()
        multiplier = FractionRef.slot()

    return Ratio


@pytest.fixture
def percentage_shape() -> type[Shape]:
    """Shape with PercentageSlot."""

    class Metrics(Shape):
        completion = PercentageRef.slot()
        discount = PercentageRef.slot()
        tax_rate = PercentageRef.slot()

    return Metrics
