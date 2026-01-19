"""Tests for view capability protocols and type guards.

Tests:
- Protocol definitions
- Type guard functions (is_*)
- Protocol detection on mock implementations
"""

from typing import ClassVar

from everykv.container import ContainerProtocol, ContainerStructure
from everykv.typing import EMPTY, Empty
from everykv.typing.view import (
    is_addable,
    is_appendable,
    is_assignable,
    is_child_observable,
    is_clearable,
    is_containable,
    is_convertible,
    is_deletable,
    is_descendants_observable,
    is_discardable,
    is_initializable,
    is_insertable,
    is_nestable,
    is_observable,
    is_poppable,
    is_removable,
    is_sizeable,
    is_subscriptable,
)
from everykv.view import ViewBase


# =============================================================================
# MOCK VIEW CLASSES FOR TESTING
# =============================================================================


class MinimalView(ViewBase):
    """Minimal view with no capabilities."""

    STRUCTURE: ClassVar[ContainerStructure] = ContainerStructure(1)
    PROTOCOL: ClassVar[ContainerProtocol] = ContainerProtocol.NONE
    CONTAINER_CLS: ClassVar[type | None] = None


class ConvertibleView(ViewBase):
    """View implementing Convertible protocol."""

    STRUCTURE: ClassVar[ContainerStructure] = ContainerStructure(2)
    PROTOCOL: ClassVar[ContainerProtocol] = ContainerProtocol.NONE
    CONTAINER_CLS: ClassVar[type | None] = None

    def extract(self) -> dict | Empty:
        return {}


class InitializableView(ViewBase):
    """View implementing Initializable protocol."""

    STRUCTURE: ClassVar[ContainerStructure] = ContainerStructure(3)
    PROTOCOL: ClassVar[ContainerProtocol] = ContainerProtocol.NONE
    CONTAINER_CLS: ClassVar[type | None] = None

    def store(self, value: object) -> None:
        pass


class SubscriptableView(ViewBase):
    """View implementing Subscriptable protocol."""

    STRUCTURE: ClassVar[ContainerStructure] = ContainerStructure(4)
    PROTOCOL: ClassVar[ContainerProtocol] = ContainerProtocol.INDEXED
    CONTAINER_CLS: ClassVar[type | None] = None

    def __getitem__(self, address: int) -> object | Empty:
        return EMPTY


class AssignableView(ViewBase):
    """View implementing Assignable protocol."""

    STRUCTURE: ClassVar[ContainerStructure] = ContainerStructure(5)
    PROTOCOL: ClassVar[ContainerProtocol] = ContainerProtocol.MUTABLE
    CONTAINER_CLS: ClassVar[type | None] = None

    def __setitem__(self, address: int, value: object) -> None:
        pass


class ContainableView(ViewBase):
    """View implementing Containable protocol."""

    STRUCTURE: ClassVar[ContainerStructure] = ContainerStructure(6)
    PROTOCOL: ClassVar[ContainerProtocol] = ContainerProtocol.NONE
    CONTAINER_CLS: ClassVar[type | None] = None

    def __contains__(self, obj: object) -> bool:
        return False


class SizeableView(ViewBase):
    """View implementing Sizeable protocol."""

    STRUCTURE: ClassVar[ContainerStructure] = ContainerStructure(7)
    PROTOCOL: ClassVar[ContainerProtocol] = ContainerProtocol.SIZED
    CONTAINER_CLS: ClassVar[type | None] = None

    def __len__(self) -> int:
        return 0


class DeletableView(ViewBase):
    """View implementing Deletable protocol."""

    STRUCTURE: ClassVar[ContainerStructure] = ContainerStructure(8)
    PROTOCOL: ClassVar[ContainerProtocol] = ContainerProtocol.MUTABLE
    CONTAINER_CLS: ClassVar[type | None] = None

    def __delitem__(self, address: int) -> None:
        pass


class ClearableView(ViewBase):
    """View implementing Clearable protocol."""

    STRUCTURE: ClassVar[ContainerStructure] = ContainerStructure(9)
    PROTOCOL: ClassVar[ContainerProtocol] = ContainerProtocol.MUTABLE
    CONTAINER_CLS: ClassVar[type | None] = None

    def clear(self) -> None:
        pass


class AppendableView(ViewBase):
    """View implementing Appendable protocol."""

    STRUCTURE: ClassVar[ContainerStructure] = ContainerStructure(10)
    PROTOCOL: ClassVar[ContainerProtocol] = ContainerProtocol.MUTABLE
    CONTAINER_CLS: ClassVar[type | None] = None

    def append(self, value: object) -> None:
        pass


class InsertableView(ViewBase):
    """View implementing Insertable protocol."""

    STRUCTURE: ClassVar[ContainerStructure] = ContainerStructure(11)
    PROTOCOL: ClassVar[ContainerProtocol] = ContainerProtocol.MUTABLE
    CONTAINER_CLS: ClassVar[type | None] = None

    def insert(self, index: int, value: object) -> None:
        pass


class PoppableView(ViewBase):
    """View implementing Poppable protocol."""

    STRUCTURE: ClassVar[ContainerStructure] = ContainerStructure(12)
    PROTOCOL: ClassVar[ContainerProtocol] = ContainerProtocol.MUTABLE
    CONTAINER_CLS: ClassVar[type | None] = None

    def pop(self, index: int = -1) -> object | Empty:
        return EMPTY


class AddableView(ViewBase):
    """View implementing Addable protocol."""

    STRUCTURE: ClassVar[ContainerStructure] = ContainerStructure(13)
    PROTOCOL: ClassVar[ContainerProtocol] = ContainerProtocol.MUTABLE
    CONTAINER_CLS: ClassVar[type | None] = None

    def add(self, value: object) -> None:
        pass


class RemovableView(ViewBase):
    """View implementing Removable protocol."""

    STRUCTURE: ClassVar[ContainerStructure] = ContainerStructure(14)
    PROTOCOL: ClassVar[ContainerProtocol] = ContainerProtocol.MUTABLE
    CONTAINER_CLS: ClassVar[type | None] = None

    def remove(self, value: object) -> None:
        pass


class DiscardableView(ViewBase):
    """View implementing Discardable protocol."""

    STRUCTURE: ClassVar[ContainerStructure] = ContainerStructure(15)
    PROTOCOL: ClassVar[ContainerProtocol] = ContainerProtocol.MUTABLE
    CONTAINER_CLS: ClassVar[type | None] = None

    def discard(self, value: object) -> None:
        pass


class NestableView(ViewBase):
    """View implementing Nestable protocol."""

    STRUCTURE: ClassVar[ContainerStructure] = ContainerStructure(16)
    PROTOCOL: ClassVar[ContainerProtocol] = ContainerProtocol.NONE
    CONTAINER_CLS: ClassVar[type | None] = None

    def open_child(self, address: str, view: type) -> ViewBase:
        raise NotImplementedError


# Note: Observable protocols require actual subscription support
# and are harder to mock without Container. Tested in functional tests.


# =============================================================================
# CONVERSION CAPABILITY TESTS
# =============================================================================


class TestConversionCapabilities:
    """Tests for Convertible and Initializable type guards."""

    def test_is_convertible_true(self) -> None:
        """Test is_convertible returns True for Convertible view."""
        view = ConvertibleView.__new__(ConvertibleView)
        assert is_convertible(view) is True

    def test_is_convertible_false(self) -> None:
        """Test is_convertible returns False for non-Convertible view."""
        view = MinimalView.__new__(MinimalView)
        assert is_convertible(view) is False

    def test_is_initializable_true(self) -> None:
        """Test is_initializable returns True for Initializable view."""
        view = InitializableView.__new__(InitializableView)
        assert is_initializable(view) is True

    def test_is_initializable_false(self) -> None:
        """Test is_initializable returns False for non-Initializable view."""
        view = MinimalView.__new__(MinimalView)
        assert is_initializable(view) is False


# =============================================================================
# ACCESS CAPABILITY TESTS
# =============================================================================


class TestAccessCapabilities:
    """Tests for Subscriptable, Assignable, Containable, Sizeable, Deletable."""

    def test_is_subscriptable_true(self) -> None:
        """Test is_subscriptable returns True for Subscriptable view."""
        view = SubscriptableView.__new__(SubscriptableView)
        assert is_subscriptable(view) is True

    def test_is_subscriptable_false(self) -> None:
        """Test is_subscriptable returns False for non-Subscriptable view."""
        view = MinimalView.__new__(MinimalView)
        assert is_subscriptable(view) is False

    def test_is_assignable_true(self) -> None:
        """Test is_assignable returns True for Assignable view."""
        view = AssignableView.__new__(AssignableView)
        assert is_assignable(view) is True

    def test_is_assignable_false(self) -> None:
        """Test is_assignable returns False for non-Assignable view."""
        view = MinimalView.__new__(MinimalView)
        assert is_assignable(view) is False

    def test_is_containable_true(self) -> None:
        """Test is_containable returns True for Containable view."""
        view = ContainableView.__new__(ContainableView)
        assert is_containable(view) is True

    def test_is_containable_false(self) -> None:
        """Test is_containable returns False for non-Containable view."""
        view = MinimalView.__new__(MinimalView)
        assert is_containable(view) is False

    def test_is_sizeable_true(self) -> None:
        """Test is_sizeable returns True for Sizeable view."""
        view = SizeableView.__new__(SizeableView)
        assert is_sizeable(view) is True

    def test_is_sizeable_false(self) -> None:
        """Test is_sizeable returns False for non-Sizeable view."""
        view = MinimalView.__new__(MinimalView)
        assert is_sizeable(view) is False

    def test_is_deletable_true(self) -> None:
        """Test is_deletable returns True for Deletable view."""
        view = DeletableView.__new__(DeletableView)
        assert is_deletable(view) is True

    def test_is_deletable_false(self) -> None:
        """Test is_deletable returns False for non-Deletable view."""
        view = MinimalView.__new__(MinimalView)
        assert is_deletable(view) is False


# =============================================================================
# MUTATION CAPABILITY TESTS
# =============================================================================


class TestMutationCapabilities:
    """Tests for mutation-related type guards."""

    def test_is_clearable_true(self) -> None:
        """Test is_clearable returns True for Clearable view."""
        view = ClearableView.__new__(ClearableView)
        assert is_clearable(view) is True

    def test_is_clearable_false(self) -> None:
        """Test is_clearable returns False for non-Clearable view."""
        view = MinimalView.__new__(MinimalView)
        assert is_clearable(view) is False

    def test_is_appendable_true(self) -> None:
        """Test is_appendable returns True for Appendable view."""
        view = AppendableView.__new__(AppendableView)
        assert is_appendable(view) is True

    def test_is_appendable_false(self) -> None:
        """Test is_appendable returns False for non-Appendable view."""
        view = MinimalView.__new__(MinimalView)
        assert is_appendable(view) is False

    def test_is_insertable_true(self) -> None:
        """Test is_insertable returns True for Insertable view."""
        view = InsertableView.__new__(InsertableView)
        assert is_insertable(view) is True

    def test_is_insertable_false(self) -> None:
        """Test is_insertable returns False for non-Insertable view."""
        view = MinimalView.__new__(MinimalView)
        assert is_insertable(view) is False

    def test_is_poppable_true(self) -> None:
        """Test is_poppable returns True for Poppable view."""
        view = PoppableView.__new__(PoppableView)
        assert is_poppable(view) is True

    def test_is_poppable_false(self) -> None:
        """Test is_poppable returns False for non-Poppable view."""
        view = MinimalView.__new__(MinimalView)
        assert is_poppable(view) is False

    def test_is_addable_true(self) -> None:
        """Test is_addable returns True for Addable view."""
        view = AddableView.__new__(AddableView)
        assert is_addable(view) is True

    def test_is_addable_false(self) -> None:
        """Test is_addable returns False for non-Addable view."""
        view = MinimalView.__new__(MinimalView)
        assert is_addable(view) is False

    def test_is_removable_true(self) -> None:
        """Test is_removable returns True for Removable view."""
        view = RemovableView.__new__(RemovableView)
        assert is_removable(view) is True

    def test_is_removable_false(self) -> None:
        """Test is_removable returns False for non-Removable view."""
        view = MinimalView.__new__(MinimalView)
        assert is_removable(view) is False

    def test_is_discardable_true(self) -> None:
        """Test is_discardable returns True for Discardable view."""
        view = DiscardableView.__new__(DiscardableView)
        assert is_discardable(view) is True

    def test_is_discardable_false(self) -> None:
        """Test is_discardable returns False for non-Discardable view."""
        view = MinimalView.__new__(MinimalView)
        assert is_discardable(view) is False


# =============================================================================
# NAVIGATION CAPABILITY TESTS
# =============================================================================


class TestNavigationCapabilities:
    """Tests for Nestable type guard."""

    def test_is_nestable_true(self) -> None:
        """Test is_nestable returns True for Nestable view."""
        view = NestableView.__new__(NestableView)
        assert is_nestable(view) is True

    def test_is_nestable_false(self) -> None:
        """Test is_nestable returns False for non-Nestable view."""
        view = MinimalView.__new__(MinimalView)
        assert is_nestable(view) is False


# =============================================================================
# TYPE GUARD ON NON-VIEW OBJECTS
# =============================================================================


class TestTypeGuardsOnNonViews:
    """Test type guards return False for non-View objects."""

    def test_type_guards_return_false_for_none(self) -> None:
        """Test all type guards return False for None."""
        assert is_convertible(None) is False
        assert is_initializable(None) is False
        assert is_subscriptable(None) is False
        assert is_assignable(None) is False
        assert is_containable(None) is False
        assert is_sizeable(None) is False
        assert is_deletable(None) is False
        assert is_clearable(None) is False
        assert is_appendable(None) is False
        assert is_insertable(None) is False
        assert is_poppable(None) is False
        assert is_addable(None) is False
        assert is_removable(None) is False
        assert is_discardable(None) is False
        assert is_nestable(None) is False
        assert is_observable(None) is False
        assert is_child_observable(None) is False
        assert is_descendants_observable(None) is False

    def test_type_guards_return_false_for_primitives(self) -> None:
        """Test type guards return False for primitive values."""
        primitives = [42, "hello", 3.14, True, [1, 2, 3], {"a": 1}]
        for value in primitives:
            assert is_convertible(value) is False
            assert is_initializable(value) is False
            assert is_nestable(value) is False
            assert is_observable(value) is False
