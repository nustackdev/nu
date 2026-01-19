"""Tests for observer exception hierarchy."""

import pytest

from everykv._exception import EveryShapeError
from everykv.storage.observer.exceptions import (
    ObserverConnectionError,
    ObserverError,
    ObserverSubscriptionError,
    ObserverValidationError,
)


class TestObserverErrorBase:
    """Test base ObserverError exception."""

    def test_observer_error_can_be_raised(self):
        """Test that ObserverError can be raised."""
        with pytest.raises(ObserverError):
            raise ObserverError()

    def test_observer_error_can_be_caught(self):
        """Test that ObserverError can be caught."""
        try:
            raise ObserverError("test error")
        except ObserverError:
            pass
        else:
            pytest.fail("ObserverError was not caught")

    def test_observer_error_message_handling(self):
        """Test that ObserverError message is stored correctly."""
        message = "Observer operation failed"
        exc = ObserverError(message)
        assert str(exc) == message

    def test_observer_error_inherits_from_everyshape_error(self):
        """Test that ObserverError inherits from EveryShapeError."""
        exc = ObserverError("test")
        assert isinstance(exc, EveryShapeError)
        assert isinstance(exc, Exception)
        assert issubclass(ObserverError, EveryShapeError)


class TestObserverConnectionError:
    """Test ObserverConnectionError exception."""

    def test_observer_connection_error_can_be_raised(self):
        """Test that ObserverConnectionError can be raised."""
        with pytest.raises(ObserverConnectionError):
            raise ObserverConnectionError()

    def test_observer_connection_error_can_be_caught(self):
        """Test that ObserverConnectionError can be caught."""
        try:
            raise ObserverConnectionError("connection failed")
        except ObserverConnectionError:
            pass
        else:
            pytest.fail("ObserverConnectionError was not caught")

    def test_observer_connection_error_caught_as_observer_error(self):
        """Test that ObserverConnectionError can be caught as ObserverError."""
        with pytest.raises(ObserverError):
            raise ObserverConnectionError()

    def test_observer_connection_error_message(self):
        """Test ObserverConnectionError message handling."""
        message = "Failed to connect to observer"
        exc = ObserverConnectionError(message)
        assert str(exc) == message

    def test_observer_connection_error_inheritance(self):
        """Test ObserverConnectionError inheritance chain."""
        exc = ObserverConnectionError("test")
        assert isinstance(exc, ObserverConnectionError)
        assert isinstance(exc, ObserverError)
        assert issubclass(ObserverConnectionError, ObserverError)


class TestObserverSubscriptionError:
    """Test ObserverSubscriptionError exception."""

    def test_observer_subscription_error_can_be_raised(self):
        """Test that ObserverSubscriptionError can be raised."""
        with pytest.raises(ObserverSubscriptionError):
            raise ObserverSubscriptionError()

    def test_observer_subscription_error_can_be_caught(self):
        """Test that ObserverSubscriptionError can be caught."""
        try:
            raise ObserverSubscriptionError("subscription failed")
        except ObserverSubscriptionError:
            pass
        else:
            pytest.fail("ObserverSubscriptionError was not caught")

    def test_observer_subscription_error_caught_as_observer_error(self):
        """Test that ObserverSubscriptionError can be caught as ObserverError."""
        with pytest.raises(ObserverError):
            raise ObserverSubscriptionError()

    def test_observer_subscription_error_message(self):
        """Test ObserverSubscriptionError message handling."""
        message = "Subscription operation failed"
        exc = ObserverSubscriptionError(message)
        assert str(exc) == message

    def test_observer_subscription_error_inheritance(self):
        """Test ObserverSubscriptionError inheritance chain."""
        exc = ObserverSubscriptionError("test")
        assert isinstance(exc, ObserverSubscriptionError)
        assert isinstance(exc, ObserverError)
        assert issubclass(ObserverSubscriptionError, ObserverError)


class TestObserverValidationError:
    """Test ObserverValidationError exception."""

    def test_observer_validation_error_can_be_raised(self):
        """Test that ObserverValidationError can be raised."""
        with pytest.raises(ObserverValidationError):
            raise ObserverValidationError()

    def test_observer_validation_error_can_be_caught(self):
        """Test that ObserverValidationError can be caught."""
        try:
            raise ObserverValidationError("validation failed")
        except ObserverValidationError:
            pass
        else:
            pytest.fail("ObserverValidationError was not caught")

    def test_observer_validation_error_caught_as_observer_error(self):
        """Test that ObserverValidationError can be caught as ObserverError."""
        with pytest.raises(ObserverError):
            raise ObserverValidationError()

    def test_observer_validation_error_message(self):
        """Test ObserverValidationError message handling."""
        message = "Validation error"
        exc = ObserverValidationError(message)
        assert str(exc) == message

    def test_observer_validation_error_inheritance(self):
        """Test ObserverValidationError inheritance chain."""
        exc = ObserverValidationError("test")
        assert isinstance(exc, ObserverValidationError)
        assert isinstance(exc, ObserverError)
        assert issubclass(ObserverValidationError, ObserverError)


class TestObserverExceptionHierarchy:
    """Test the overall observer exception hierarchy and relationships."""

    def test_all_exceptions_inherit_from_observer_error(self):
        """Test that all observer exceptions inherit from ObserverError."""
        exceptions = [
            ObserverConnectionError,
            ObserverSubscriptionError,
            ObserverValidationError,
        ]
        for exc_class in exceptions:
            assert issubclass(exc_class, ObserverError), (
                f"{exc_class.__name__} should inherit from ObserverError"
            )

    def test_all_exceptions_inherit_from_everyshape_error(self):
        """Test that all observer exceptions inherit from EveryShapeError."""
        exceptions = [
            ObserverError,
            ObserverConnectionError,
            ObserverSubscriptionError,
            ObserverValidationError,
        ]
        for exc_class in exceptions:
            assert issubclass(exc_class, EveryShapeError), (
                f"{exc_class.__name__} should inherit from EveryShapeError"
            )

    def test_catch_multiple_exception_types(self):
        """Test catching multiple observer exception types."""
        # ObserverConnectionError should be catchable as both types
        with pytest.raises((ObserverError, ObserverConnectionError)):
            raise ObserverConnectionError("connection failed")

        # ObserverSubscriptionError should be catchable as both types
        with pytest.raises((ObserverError, ObserverSubscriptionError)):
            raise ObserverSubscriptionError("subscription failed")

        # ObserverValidationError should be catchable as both types
        with pytest.raises((ObserverError, ObserverValidationError)):
            raise ObserverValidationError("validation failed")

    def test_exception_mro(self):
        """Test Method Resolution Order (MRO) for observer exceptions."""
        # ObserverConnectionError MRO should include ObserverError
        mro = ObserverConnectionError.__mro__
        assert ObserverError in mro
        assert EveryShapeError in mro
        assert Exception in mro

        # ObserverSubscriptionError MRO should include ObserverError
        mro = ObserverSubscriptionError.__mro__
        assert ObserverError in mro
        assert EveryShapeError in mro
        assert Exception in mro

        # ObserverValidationError MRO should include ObserverError
        mro = ObserverValidationError.__mro__
        assert ObserverError in mro
        assert EveryShapeError in mro
        assert Exception in mro
