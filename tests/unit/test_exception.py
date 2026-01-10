"""Tests for everyshape._exception module."""

import pytest

from everyshape._exception import EveryShapeError


class TestEveryShapeError:
    """Test cases for EveryShapeError exception class."""

    def test_exception_can_be_raised(self):
        """Test that EveryShapeError can be raised."""
        with pytest.raises(EveryShapeError):
            raise EveryShapeError()

    def test_exception_can_be_caught(self):
        """Test that EveryShapeError can be caught."""
        try:
            raise EveryShapeError("test error")
        except EveryShapeError:
            # Exception was caught successfully
            pass
        else:
            pytest.fail("EveryShapeError was not caught")

    def test_exception_message_handling(self):
        """Test that exception message is stored and retrieved correctly."""
        error_message = "This is a test error message"
        exc = EveryShapeError(error_message)
        assert str(exc) == error_message

    def test_exception_with_empty_message(self):
        """Test exception with empty message."""
        exc = EveryShapeError()
        assert str(exc) == ""

    def test_exception_is_instance_of_exception(self):
        """Test that EveryShapeError is an instance of Exception."""
        exc = EveryShapeError()
        assert isinstance(exc, Exception)
        assert isinstance(exc, EveryShapeError)

    def test_exception_inheritance_chain(self):
        """Test the inheritance chain of EveryShapeError."""
        exc = EveryShapeError("test")
        assert issubclass(EveryShapeError, Exception)
        assert isinstance(exc, BaseException)
