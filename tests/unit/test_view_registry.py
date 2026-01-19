"""Unit tests for ViewRegistry.

Tests:
- View registration
- Structure ID lookup
- Container type lookup
- Error handling for duplicates and missing registrations
"""

from typing import ClassVar

import pytest

from everykv.container import ContainerProtocol, ContainerStructure
from everykv.view import ViewBase, ViewRegistry, ViewRegistryError


# =============================================================================
# TEST VIEW CLASSES
# =============================================================================


class MockDictView(ViewBase):
    """Mock dict-like view for testing."""

    STRUCTURE: ClassVar[ContainerStructure] = ContainerStructure(1)
    PROTOCOL: ClassVar[ContainerProtocol] = ContainerProtocol.MAPPING
    CONTAINER_CLS: ClassVar[type] = dict


class MockListView(ViewBase):
    """Mock list-like view for testing."""

    STRUCTURE: ClassVar[ContainerStructure] = ContainerStructure(2)
    PROTOCOL: ClassVar[ContainerProtocol] = ContainerProtocol.INDEXED
    CONTAINER_CLS: ClassVar[type] = list


class MockSetView(ViewBase):
    """Mock set-like view for testing."""

    STRUCTURE: ClassVar[ContainerStructure] = ContainerStructure(3)
    PROTOCOL: ClassVar[ContainerProtocol] = ContainerProtocol.NONE
    CONTAINER_CLS: ClassVar[type] = set


class MockCustomView(ViewBase):
    """Mock view without container type (custom container)."""

    STRUCTURE: ClassVar[ContainerStructure] = ContainerStructure(100)
    PROTOCOL: ClassVar[ContainerProtocol] = ContainerProtocol.MUTABLE
    CONTAINER_CLS: ClassVar[type | None] = None


# =============================================================================
# REGISTRATION TESTS
# =============================================================================


class TestViewRegistration:
    """Tests for view registration."""

    def test_register_single_view(self) -> None:
        """Test registering a single view."""
        registry = ViewRegistry()
        registry.register(MockDictView)

        # Should be retrievable by structure
        assert registry.get_view_for_structure(ContainerStructure(1)) is MockDictView

    def test_register_multiple_views(self) -> None:
        """Test registering multiple views."""
        registry = ViewRegistry()
        registry.register(MockDictView)
        registry.register(MockListView)
        registry.register(MockSetView)

        assert registry.get_view_for_structure(ContainerStructure(1)) is MockDictView
        assert registry.get_view_for_structure(ContainerStructure(2)) is MockListView
        assert registry.get_view_for_structure(ContainerStructure(3)) is MockSetView

    def test_register_view_without_container_type(self) -> None:
        """Test registering view with no container type."""
        registry = ViewRegistry()
        registry.register(MockCustomView)

        # Should be retrievable by structure
        assert registry.get_view_for_structure(ContainerStructure(100)) is MockCustomView

    def test_register_duplicate_structure_id_raises(self) -> None:
        """Test registering duplicate structure ID raises error."""
        registry = ViewRegistry()
        registry.register(MockDictView)

        # Create another view with same structure ID
        class DuplicateView(ViewBase):
            STRUCTURE: ClassVar[ContainerStructure] = ContainerStructure(1)
            PROTOCOL: ClassVar[ContainerProtocol] = ContainerProtocol.NONE
            CONTAINER_CLS: ClassVar[type | None] = None

        with pytest.raises(ViewRegistryError, match=r"Structure ID.*already registered"):
            registry.register(DuplicateView)

    def test_register_duplicate_container_type_raises(self) -> None:
        """Test registering duplicate container type raises error."""
        registry = ViewRegistry()
        registry.register(MockDictView)

        # Create another view with same container type
        class DuplicateDictView(ViewBase):
            STRUCTURE: ClassVar[ContainerStructure] = ContainerStructure(999)
            PROTOCOL: ClassVar[ContainerProtocol] = ContainerProtocol.NONE
            CONTAINER_CLS: ClassVar[type] = dict

        with pytest.raises(ViewRegistryError, match=r"Container type.*already registered"):
            registry.register(DuplicateDictView)


# =============================================================================
# STRUCTURE LOOKUP TESTS
# =============================================================================


class TestStructureLookup:
    """Tests for structure ID lookup."""

    def test_get_view_for_structure_found(self) -> None:
        """Test getting view by structure ID when registered."""
        registry = ViewRegistry()
        registry.register(MockDictView)

        view = registry.get_view_for_structure(ContainerStructure(1))
        assert view is MockDictView

    def test_get_view_for_structure_not_found_raises(self) -> None:
        """Test getting view by structure ID when not registered raises."""
        registry = ViewRegistry()

        with pytest.raises(ViewRegistryError, match="No view registered for structure ID"):
            registry.get_view_for_structure(ContainerStructure(999))

    def test_get_view_for_structure_after_multiple_registrations(self) -> None:
        """Test structure lookup with multiple registrations."""
        registry = ViewRegistry()
        registry.register(MockDictView)
        registry.register(MockListView)
        registry.register(MockSetView)

        # Each structure ID returns correct view
        assert registry.get_view_for_structure(ContainerStructure(1)) is MockDictView
        assert registry.get_view_for_structure(ContainerStructure(2)) is MockListView
        assert registry.get_view_for_structure(ContainerStructure(3)) is MockSetView


# =============================================================================
# TYPE LOOKUP TESTS
# =============================================================================


class TestTypeLookup:
    """Tests for container type lookup."""

    def test_get_view_for_type_exact_match(self) -> None:
        """Test getting view by exact type match."""
        registry = ViewRegistry()
        registry.register(MockDictView)

        view = registry.get_view_for_type(dict)
        assert view is MockDictView

    def test_get_view_for_type_not_found_raises(self) -> None:
        """Test getting view by type when not registered raises."""
        registry = ViewRegistry()

        with pytest.raises(ViewRegistryError, match="No view registered for type"):
            registry.get_view_for_type(dict)

    def test_get_view_for_type_subclass_match(self) -> None:
        """Test getting view for subclass of registered type."""
        registry = ViewRegistry()
        registry.register(MockDictView)

        # OrderedDict is subclass of dict
        from collections import OrderedDict

        view = registry.get_view_for_type(OrderedDict)
        assert view is MockDictView

    def test_get_view_for_type_no_container_type_raises(self) -> None:
        """Test getting view by type for view without container type raises."""
        registry = ViewRegistry()
        registry.register(MockCustomView)

        # Cannot lookup by type for views without container_cls
        with pytest.raises(ViewRegistryError):
            registry.get_view_for_type(object)


# =============================================================================
# STRUCTURE FOR TYPE TESTS
# =============================================================================


class TestStructureForType:
    """Tests for get_structure_for_type."""

    def test_get_structure_for_type_found(self) -> None:
        """Test getting structure ID for registered type."""
        registry = ViewRegistry()
        registry.register(MockDictView)

        structure_id = registry.get_structure_for_type(dict)
        assert structure_id == 1

    def test_get_structure_for_type_not_found_raises(self) -> None:
        """Test getting structure ID for unregistered type raises."""
        registry = ViewRegistry()

        with pytest.raises(ViewRegistryError, match="No registration for type"):
            registry.get_structure_for_type(dict)


# =============================================================================
# IS CONTAINER TYPE TESTS
# =============================================================================


class TestIsContainerType:
    """Tests for is_container_type check."""

    def test_is_container_type_true(self) -> None:
        """Test is_container_type returns True for registered types."""
        registry = ViewRegistry()
        registry.register(MockDictView)
        registry.register(MockListView)

        assert registry.is_container_type({"a": 1}) is True
        assert registry.is_container_type([1, 2, 3]) is True

    def test_is_container_type_false_unregistered(self) -> None:
        """Test is_container_type returns False for unregistered types."""
        registry = ViewRegistry()
        registry.register(MockDictView)

        # list not registered
        assert registry.is_container_type([1, 2, 3]) is False

    def test_is_container_type_false_primitive(self) -> None:
        """Test is_container_type returns False for primitives."""
        registry = ViewRegistry()
        registry.register(MockDictView)
        registry.register(MockListView)

        assert registry.is_container_type(42) is False
        assert registry.is_container_type("hello") is False
        assert registry.is_container_type(3.14) is False
        assert registry.is_container_type(None) is False

    def test_is_container_type_empty_registry(self) -> None:
        """Test is_container_type returns False with empty registry."""
        registry = ViewRegistry()

        assert registry.is_container_type({"a": 1}) is False
        assert registry.is_container_type([1, 2]) is False
