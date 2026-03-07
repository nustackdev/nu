"""Fixtures for view layer testing."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

import pytest
from virtuals.codecs import NoOpCodec
from virtuals.storages.mem import InMemoryStorage

from eb_pv.views import DictView


if TYPE_CHECKING:
    from collections.abc import Callable, Generator

    from virtuals.tkv.storage import SnapshotProtocol, StorageProtocol, TransactionProtocol
    from virtuals.view import View


# =============================================================================
# FIXTURES
# =============================================================================


@pytest.fixture
def storage() -> Generator[StorageProtocol, None, None]:
    """Memory storage instance for functional tests.

    Provides a clean storage instance for each test with automatic cleanup.
    """
    # No-op codec
    storage = InMemoryStorage(codec=NoOpCodec())
    storage.open()
    try:
        yield storage
    finally:
        storage.close()


@pytest.fixture
def tx(storage: StorageProtocol) -> Generator[TransactionProtocol, None, None]:
    """Read-write transaction context.

    Auto-commits on successful completion, rolls back on exception.
    """
    with storage.transaction() as transaction:
        yield transaction


@pytest.fixture
def snapshot(storage: StorageProtocol) -> Generator[SnapshotProtocol, None, None]:
    """Read-only snapshot context.

    Useful for testing isolation and concurrent read scenarios.
    """
    with storage.snapshot() as snap:
        yield snap


@pytest.fixture
def root_view(tx: TransactionProtocol) -> DictView:
    """Create a DictView at root for testing."""
    return DictView.open_root(tx)


# ============================================================================
# View Factories
# ============================================================================


@pytest.fixture
def dict_factory(root_view: DictView) -> Callable[[str, dict[str, Any] | None], View]:
    """Factory for creating DictViews with test data.

    Navigates from root_view using open_child() to create child DictView.

    Usage:
        def test_example(dict_factory):
            users = dict_factory("users", {"alice": {"name": "Alice"}})
            assert "alice" in users
    """

    def _create(address: str, data: dict | None = None) -> View:
        from eb_pv.views import DictView

        view = root_view.open_child(address, DictView)
        if data is not None:
            view.store(data)
        return view

    return _create


@pytest.fixture
def list_factory(root_view: DictView) -> Callable[[str, list[Any] | None], View]:
    """Factory for creating ListViews with test data.

    Navigates from root_view using open_child() to create child ListView.

    Usage:
        def test_example(list_factory):
            items = list_factory("items", [1, 2, 3])
            assert len(items) == 3
    """

    def _create(address: str, data: list | None = None) -> View:
        from eb_pv.views import ListView

        view = root_view.open_child(address, ListView)
        if data is not None:
            view.store(data)
        return view

    return _create


@pytest.fixture
def set_factory(root_view: DictView) -> Callable[[str, set[Any] | None], View]:
    """Factory for creating SetViews with test data.

    Navigates from root_view using open_child() to create child SetView.

    Usage:
        def test_example(set_factory):
            tags = set_factory("tags", {"python", "rust"})
            assert "python" in tags
    """

    def _create(address: str, data: set | None = None) -> View:
        from eb_pv.views import SetView

        view = root_view.open_child(address, SetView)
        if data is not None:
            view.store(data)
        return view

    return _create


@pytest.fixture
def tuple_factory(root_view: DictView) -> Callable[[str, tuple[Any, ...] | None], View]:
    """Factory for creating TupleViews with test data.

    Navigates from root_view using open_child() to create child TupleView.

    Usage:
        def test_example(tuple_factory):
            coords = tuple_factory("coords", (10, 20, 30))
            assert coords[0] == 10
    """

    def _create(address: str, data: tuple | None = None) -> View:
        from eb_pv.views import TupleView

        view = root_view.open_child(address, TupleView)
        if data is not None:
            view.store(data)
        return view

    return _create
