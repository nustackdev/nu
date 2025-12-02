"""Fixtures for view layer testing."""

from collections.abc import Callable
from typing import Any

import pytest
from esstd.collections import DictView

from everyshape.view import View


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

    def _create(address: str, data: dict[str, Any] | None = None) -> View:
        from esstd.collections import DictView

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

    def _create(address: str, data: list[Any] | None = None) -> View:
        from esstd.collections import ListView

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

    def _create(address: str, data: set[Any] | None = None) -> View:
        from esstd.collections import SetView

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

    def _create(address: str, data: tuple[Any, ...] | None = None) -> View:
        from esstd.collections import TupleView

        view = root_view.open_child(address, TupleView)
        if data is not None:
            view.store(data)
        return view

    return _create
