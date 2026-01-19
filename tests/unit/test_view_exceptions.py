"""Tests for view layer exception hierarchy.

Tests:
- ViewError base exception
- ViewRegistryError
- ViewOperationError
- Exception inheritance chain
"""

import pytest

from everykv._exception import EveryShapeError
from everykv.view import ViewError, ViewOperationError, ViewRegistryError


# =============================================================================
# VIEW ERROR BASE
# =============================================================================


class TestViewError:
    """Test cases for ViewError base exception."""

    def test_exception_can_be_raised(self) -> None:
        """Test that ViewError can be raised."""
        with pytest.raises(ViewError):
            raise ViewError()

    def test_exception_can_be_caught(self) -> None:
        """Test that ViewError can be caught."""
        try:
            raise ViewError("test error")
        except ViewError:
            pass
        else:
            pytest.fail("ViewError was not caught")

    def test_exception_message_handling(self) -> None:
        """Test that exception message is stored correctly."""
        error_message = "This is a test view error"
        exc = ViewError(error_message)
        assert str(exc) == error_message

    def test_exception_with_empty_message(self) -> None:
        """Test exception with empty message."""
        exc = ViewError()
        assert str(exc) == ""

    def test_inherits_from_everyshape_error(self) -> None:
        """Test that ViewError inherits from EveryShapeError."""
        exc = ViewError()
        assert isinstance(exc, EveryShapeError)
        assert isinstance(exc, Exception)
        assert issubclass(ViewError, EveryShapeError)

    def test_caught_as_everyshape_error(self) -> None:
        """Test ViewError can be caught as EveryShapeError."""
        try:
            raise ViewError("view error")
        except EveryShapeError as e:
            assert str(e) == "view error"


# =============================================================================
# VIEW REGISTRY ERROR
# =============================================================================


class TestViewRegistryError:
    """Test cases for ViewRegistryError exception."""

    def test_exception_can_be_raised(self) -> None:
        """Test that ViewRegistryError can be raised."""
        with pytest.raises(ViewRegistryError):
            raise ViewRegistryError()

    def test_exception_can_be_caught(self) -> None:
        """Test that ViewRegistryError can be caught."""
        try:
            raise ViewRegistryError("registry error")
        except ViewRegistryError:
            pass
        else:
            pytest.fail("ViewRegistryError was not caught")

    def test_exception_message_handling(self) -> None:
        """Test that exception message is stored correctly."""
        error_message = "View already registered"
        exc = ViewRegistryError(error_message)
        assert str(exc) == error_message

    def test_inherits_from_view_error(self) -> None:
        """Test that ViewRegistryError inherits from ViewError."""
        exc = ViewRegistryError()
        assert isinstance(exc, ViewError)
        assert isinstance(exc, EveryShapeError)
        assert issubclass(ViewRegistryError, ViewError)

    def test_caught_as_view_error(self) -> None:
        """Test ViewRegistryError can be caught as ViewError."""
        try:
            raise ViewRegistryError("registry error")
        except ViewError as e:
            assert str(e) == "registry error"


# =============================================================================
# VIEW OPERATION ERROR
# =============================================================================


class TestViewOperationError:
    """Test cases for ViewOperationError exception."""

    def test_exception_can_be_raised(self) -> None:
        """Test that ViewOperationError can be raised."""
        with pytest.raises(ViewOperationError):
            raise ViewOperationError()

    def test_exception_can_be_caught(self) -> None:
        """Test that ViewOperationError can be caught."""
        try:
            raise ViewOperationError("operation error")
        except ViewOperationError:
            pass
        else:
            pytest.fail("ViewOperationError was not caught")

    def test_exception_message_handling(self) -> None:
        """Test that exception message is stored correctly."""
        error_message = "View operation failed"
        exc = ViewOperationError(error_message)
        assert str(exc) == error_message

    def test_inherits_from_view_error(self) -> None:
        """Test that ViewOperationError inherits from ViewError."""
        exc = ViewOperationError()
        assert isinstance(exc, ViewError)
        assert isinstance(exc, EveryShapeError)
        assert issubclass(ViewOperationError, ViewError)

    def test_caught_as_view_error(self) -> None:
        """Test ViewOperationError can be caught as ViewError."""
        try:
            raise ViewOperationError("operation error")
        except ViewError as e:
            assert str(e) == "operation error"


# =============================================================================
# EXCEPTION HIERARCHY
# =============================================================================


class TestViewExceptionHierarchy:
    """Test the complete view exception hierarchy."""

    def test_all_view_exceptions_inherit_from_view_error(self) -> None:
        """Test all view exceptions inherit from ViewError."""
        assert issubclass(ViewRegistryError, ViewError)
        assert issubclass(ViewOperationError, ViewError)

    def test_all_view_exceptions_inherit_from_everyshape_error(self) -> None:
        """Test all view exceptions inherit from EveryShapeError."""
        assert issubclass(ViewError, EveryShapeError)
        assert issubclass(ViewRegistryError, EveryShapeError)
        assert issubclass(ViewOperationError, EveryShapeError)

    def test_catching_view_error_catches_all_subclasses(self) -> None:
        """Test catching ViewError catches all view exceptions."""
        exceptions = [
            ViewError("base"),
            ViewRegistryError("registry"),
            ViewOperationError("operation"),
        ]

        for exc in exceptions:
            try:
                raise exc
            except ViewError:
                pass  # All should be caught
            else:
                pytest.fail(f"{type(exc).__name__} was not caught as ViewError")
