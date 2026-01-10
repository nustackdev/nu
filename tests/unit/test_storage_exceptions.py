"""Tests for storage exception hierarchy."""

import pytest

from everyshape._exception import EveryShapeError
from everyshape.storage.storage.exceptions import (
    StorageClosedError,
    StorageDeleteError,
    StorageError,
    StorageInterfaceError,
    StorageIteratorError,
    StorageKeyError,
    StorageLookupError,
    StorageOperationError,
    StorageTransactionAbortedError,
    StorageTransactionConflictError,
    StorageTransactionError,
    StorageWriteError,
)


class TestStorageErrorBase:
    """Test base StorageError exception."""

    def test_storage_error_can_be_raised(self):
        """Test that StorageError can be raised."""
        with pytest.raises(StorageError):
            raise StorageError()

    def test_storage_error_can_be_caught(self):
        """Test that StorageError can be caught."""
        try:
            raise StorageError("test error")
        except StorageError:
            pass
        else:
            pytest.fail("StorageError was not caught")

    def test_storage_error_message_handling(self):
        """Test that StorageError message is stored correctly."""
        message = "Storage operation failed"
        exc = StorageError(message)
        assert str(exc) == message

    def test_storage_error_inherits_from_everyshape_error(self):
        """Test that StorageError inherits from EveryShapeError."""
        exc = StorageError("test")
        assert isinstance(exc, EveryShapeError)
        assert isinstance(exc, Exception)
        assert issubclass(StorageError, EveryShapeError)


class TestStorageInterfaceError:
    """Test StorageInterfaceError exception."""

    def test_storage_interface_error_can_be_raised(self):
        """Test that StorageInterfaceError can be raised."""
        with pytest.raises(StorageInterfaceError):
            raise StorageInterfaceError()

    def test_storage_interface_error_can_be_caught(self):
        """Test that StorageInterfaceError can be caught."""
        try:
            raise StorageInterfaceError("invalid operation")
        except StorageInterfaceError:
            pass
        else:
            pytest.fail("StorageInterfaceError was not caught")

    def test_storage_interface_error_caught_as_storage_error(self):
        """Test that StorageInterfaceError can be caught as StorageError."""
        with pytest.raises(StorageError):
            raise StorageInterfaceError()

    def test_storage_interface_error_inheritance(self):
        """Test StorageInterfaceError inheritance chain."""
        exc = StorageInterfaceError("test")
        assert isinstance(exc, StorageInterfaceError)
        assert isinstance(exc, StorageError)
        assert issubclass(StorageInterfaceError, StorageError)


class TestStorageOperationError:
    """Test StorageOperationError exception."""

    def test_storage_operation_error_can_be_raised(self):
        """Test that StorageOperationError can be raised."""
        with pytest.raises(StorageOperationError):
            raise StorageOperationError()

    def test_storage_operation_error_message(self):
        """Test StorageOperationError message handling."""
        message = "Operation failed"
        exc = StorageOperationError(message)
        assert str(exc) == message

    def test_storage_operation_error_inheritance(self):
        """Test StorageOperationError inheritance chain."""
        exc = StorageOperationError("test")
        assert isinstance(exc, StorageOperationError)
        assert isinstance(exc, StorageError)
        assert issubclass(StorageOperationError, StorageError)


class TestStorageKeyError:
    """Test StorageKeyError exception with multiple inheritance."""

    def test_storage_key_error_can_be_raised(self):
        """Test that StorageKeyError can be raised."""
        with pytest.raises(StorageKeyError):
            raise StorageKeyError()

    def test_storage_key_error_can_be_caught_as_storage_error(self):
        """Test that StorageKeyError can be caught as StorageError."""
        with pytest.raises(StorageError):
            raise StorageKeyError("key not found")

    def test_storage_key_error_can_be_caught_as_key_error(self):
        """Test that StorageKeyError can be caught as KeyError."""
        with pytest.raises(KeyError):
            raise StorageKeyError("missing_key")

    def test_storage_key_error_message(self):
        """Test StorageKeyError message handling."""
        message = "Key 'xyz' not found"
        exc = StorageKeyError(message)
        # KeyError wraps the message in quotes
        assert message in str(exc)

    def test_storage_key_error_multiple_inheritance_storage_error(self):
        """Test StorageKeyError inherits from StorageError."""
        exc = StorageKeyError("test")
        assert isinstance(exc, StorageKeyError)
        assert isinstance(exc, StorageError)
        assert issubclass(StorageKeyError, StorageError)

    def test_storage_key_error_multiple_inheritance_key_error(self):
        """Test StorageKeyError inherits from KeyError."""
        exc = StorageKeyError("test")
        assert isinstance(exc, StorageKeyError)
        assert isinstance(exc, KeyError)
        assert issubclass(StorageKeyError, KeyError)

    def test_storage_key_error_inheritance_chain(self):
        """Test StorageKeyError full inheritance chain."""
        exc = StorageKeyError("test")
        assert isinstance(exc, StorageKeyError)
        assert isinstance(exc, StorageError)
        assert isinstance(exc, KeyError)
        assert isinstance(exc, Exception)


class TestStorageLookupError:
    """Test StorageLookupError exception with multiple inheritance."""

    def test_storage_lookup_error_can_be_raised(self):
        """Test that StorageLookupError can be raised."""
        with pytest.raises(StorageLookupError):
            raise StorageLookupError()

    def test_storage_lookup_error_can_be_caught_as_storage_operation_error(
        self,
    ):
        """Test that StorageLookupError can be caught as StorageOperationError."""
        with pytest.raises(StorageOperationError):
            raise StorageLookupError("lookup failed")

    def test_storage_lookup_error_can_be_caught_as_lookup_error(self):
        """Test that StorageLookupError can be caught as LookupError."""
        with pytest.raises(LookupError):
            raise StorageLookupError("not found")

    def test_storage_lookup_error_message(self):
        """Test StorageLookupError message handling."""
        message = "Lookup operation failed"
        exc = StorageLookupError(message)
        assert str(exc) == message

    def test_storage_lookup_error_multiple_inheritance_operation_error(self):
        """Test StorageLookupError inherits from StorageOperationError."""
        exc = StorageLookupError("test")
        assert isinstance(exc, StorageLookupError)
        assert isinstance(exc, StorageOperationError)
        assert issubclass(StorageLookupError, StorageOperationError)

    def test_storage_lookup_error_multiple_inheritance_lookup_error(self):
        """Test StorageLookupError inherits from LookupError."""
        exc = StorageLookupError("test")
        assert isinstance(exc, StorageLookupError)
        assert isinstance(exc, LookupError)
        assert issubclass(StorageLookupError, LookupError)

    def test_storage_lookup_error_inheritance_chain(self):
        """Test StorageLookupError full inheritance chain."""
        exc = StorageLookupError("test")
        assert isinstance(exc, StorageLookupError)
        assert isinstance(exc, StorageOperationError)
        assert isinstance(exc, StorageError)
        assert isinstance(exc, LookupError)
        assert isinstance(exc, Exception)


class TestStorageWriteError:
    """Test StorageWriteError exception."""

    def test_storage_write_error_can_be_raised(self):
        """Test that StorageWriteError can be raised."""
        with pytest.raises(StorageWriteError):
            raise StorageWriteError()

    def test_storage_write_error_caught_as_operation_error(self):
        """Test that StorageWriteError can be caught as StorageOperationError."""
        with pytest.raises(StorageOperationError):
            raise StorageWriteError("write failed")

    def test_storage_write_error_message(self):
        """Test StorageWriteError message handling."""
        message = "Failed to write data"
        exc = StorageWriteError(message)
        assert str(exc) == message

    def test_storage_write_error_inheritance(self):
        """Test StorageWriteError inheritance chain."""
        exc = StorageWriteError("test")
        assert isinstance(exc, StorageWriteError)
        assert isinstance(exc, StorageOperationError)
        assert isinstance(exc, StorageError)
        assert issubclass(StorageWriteError, StorageOperationError)


class TestStorageDeleteError:
    """Test StorageDeleteError exception."""

    def test_storage_delete_error_can_be_raised(self):
        """Test that StorageDeleteError can be raised."""
        with pytest.raises(StorageDeleteError):
            raise StorageDeleteError()

    def test_storage_delete_error_caught_as_write_error(self):
        """Test that StorageDeleteError can be caught as StorageWriteError."""
        with pytest.raises(StorageWriteError):
            raise StorageDeleteError("delete failed")

    def test_storage_delete_error_caught_as_operation_error(self):
        """Test that StorageDeleteError can be caught as StorageOperationError."""
        with pytest.raises(StorageOperationError):
            raise StorageDeleteError("delete failed")

    def test_storage_delete_error_message(self):
        """Test StorageDeleteError message handling."""
        message = "Failed to delete key"
        exc = StorageDeleteError(message)
        assert str(exc) == message

    def test_storage_delete_error_inheritance(self):
        """Test StorageDeleteError inheritance chain."""
        exc = StorageDeleteError("test")
        assert isinstance(exc, StorageDeleteError)
        assert isinstance(exc, StorageWriteError)
        assert isinstance(exc, StorageOperationError)
        assert isinstance(exc, StorageError)
        assert issubclass(StorageDeleteError, StorageWriteError)


class TestStorageTransactionError:
    """Test StorageTransactionError exception."""

    def test_storage_transaction_error_can_be_raised(self):
        """Test that StorageTransactionError can be raised."""
        with pytest.raises(StorageTransactionError):
            raise StorageTransactionError()

    def test_storage_transaction_error_caught_as_storage_error(self):
        """Test that StorageTransactionError can be caught as StorageError."""
        with pytest.raises(StorageError):
            raise StorageTransactionError("transaction failed")

    def test_storage_transaction_error_message(self):
        """Test StorageTransactionError message handling."""
        message = "Transaction error"
        exc = StorageTransactionError(message)
        assert str(exc) == message

    def test_storage_transaction_error_inheritance(self):
        """Test StorageTransactionError inheritance chain."""
        exc = StorageTransactionError("test")
        assert isinstance(exc, StorageTransactionError)
        assert isinstance(exc, StorageError)
        assert issubclass(StorageTransactionError, StorageError)


class TestStorageTransactionConflictError:
    """Test StorageTransactionConflictError exception."""

    def test_storage_transaction_conflict_error_can_be_raised(self):
        """Test that StorageTransactionConflictError can be raised."""
        with pytest.raises(StorageTransactionConflictError):
            raise StorageTransactionConflictError()

    def test_storage_transaction_conflict_error_caught_as_transaction_error(self):
        """Test that StorageTransactionConflictError can be caught as StorageTransactionError."""
        with pytest.raises(StorageTransactionError):
            raise StorageTransactionConflictError("conflict detected")

    def test_storage_transaction_conflict_error_message(self):
        """Test StorageTransactionConflictError message handling."""
        message = "Conflicting modifications detected"
        exc = StorageTransactionConflictError(message)
        assert str(exc) == message

    def test_storage_transaction_conflict_error_inheritance(self):
        """Test StorageTransactionConflictError inheritance chain."""
        exc = StorageTransactionConflictError("test")
        assert isinstance(exc, StorageTransactionConflictError)
        assert isinstance(exc, StorageTransactionError)
        assert isinstance(exc, StorageError)
        assert issubclass(StorageTransactionConflictError, StorageTransactionError)


class TestStorageTransactionAbortedError:
    """Test StorageTransactionAbortedError exception."""

    def test_storage_transaction_aborted_error_can_be_raised(self):
        """Test that StorageTransactionAbortedError can be raised."""
        with pytest.raises(StorageTransactionAbortedError):
            raise StorageTransactionAbortedError()

    def test_storage_transaction_aborted_error_caught_as_transaction_error(
        self,
    ):
        """Test that StorageTransactionAbortedError can be caught as StorageTransactionError."""
        with pytest.raises(StorageTransactionError):
            raise StorageTransactionAbortedError("transaction aborted")

    def test_storage_transaction_aborted_error_message(self):
        """Test StorageTransactionAbortedError message handling."""
        message = "Transaction was aborted"
        exc = StorageTransactionAbortedError(message)
        assert str(exc) == message

    def test_storage_transaction_aborted_error_inheritance(self):
        """Test StorageTransactionAbortedError inheritance chain."""
        exc = StorageTransactionAbortedError("test")
        assert isinstance(exc, StorageTransactionAbortedError)
        assert isinstance(exc, StorageTransactionError)
        assert isinstance(exc, StorageError)
        assert issubclass(StorageTransactionAbortedError, StorageTransactionError)


class TestStorageClosedError:
    """Test StorageClosedError exception."""

    def test_storage_closed_error_can_be_raised(self):
        """Test that StorageClosedError can be raised."""
        with pytest.raises(StorageClosedError):
            raise StorageClosedError()

    def test_storage_closed_error_caught_as_storage_error(self):
        """Test that StorageClosedError can be caught as StorageError."""
        with pytest.raises(StorageError):
            raise StorageClosedError("resource closed")

    def test_storage_closed_error_message(self):
        """Test StorageClosedError message handling."""
        message = "Storage resource is closed"
        exc = StorageClosedError(message)
        assert str(exc) == message

    def test_storage_closed_error_inheritance(self):
        """Test StorageClosedError inheritance chain."""
        exc = StorageClosedError("test")
        assert isinstance(exc, StorageClosedError)
        assert isinstance(exc, StorageError)
        assert issubclass(StorageClosedError, StorageError)


class TestStorageIteratorError:
    """Test StorageIteratorError exception."""

    def test_storage_iterator_error_can_be_raised(self):
        """Test that StorageIteratorError can be raised."""
        with pytest.raises(StorageIteratorError):
            raise StorageIteratorError()

    def test_storage_iterator_error_caught_as_storage_error(self):
        """Test that StorageIteratorError can be caught as StorageError."""
        with pytest.raises(StorageError):
            raise StorageIteratorError("iterator failed")

    def test_storage_iterator_error_message(self):
        """Test StorageIteratorError message handling."""
        message = "Iterator operation failed"
        exc = StorageIteratorError(message)
        assert str(exc) == message

    def test_storage_iterator_error_inheritance(self):
        """Test StorageIteratorError inheritance chain."""
        exc = StorageIteratorError("test")
        assert isinstance(exc, StorageIteratorError)
        assert isinstance(exc, StorageError)
        assert issubclass(StorageIteratorError, StorageError)


class TestExceptionHierarchy:
    """Test the overall exception hierarchy and relationships."""

    def test_all_exceptions_inherit_from_storage_error(self):
        """Test that all storage exceptions inherit from StorageError."""
        exceptions = [
            StorageInterfaceError,
            StorageOperationError,
            StorageKeyError,
            StorageLookupError,
            StorageWriteError,
            StorageDeleteError,
            StorageTransactionError,
            StorageTransactionConflictError,
            StorageTransactionAbortedError,
            StorageClosedError,
            StorageIteratorError,
        ]
        for exc_class in exceptions:
            assert issubclass(exc_class, StorageError), (
                f"{exc_class.__name__} should inherit from StorageError"
            )

    def test_write_error_hierarchy(self):
        """Test StorageWriteError and StorageDeleteError hierarchy."""
        assert issubclass(StorageDeleteError, StorageWriteError)
        assert issubclass(StorageWriteError, StorageOperationError)

    def test_transaction_error_hierarchy(self):
        """Test StorageTransactionError and its subclasses hierarchy."""
        assert issubclass(StorageTransactionConflictError, StorageTransactionError)
        assert issubclass(StorageTransactionAbortedError, StorageTransactionError)

    def test_catch_multiple_exception_types(self):
        """Test catching multiple exception types with multiple inheritance."""
        # StorageKeyError should be catchable as both StorageError and KeyError
        with pytest.raises((StorageError, KeyError)):
            raise StorageKeyError("key error")

        # StorageLookupError should be catchable as both StorageOperationError and LookupError
        with pytest.raises((StorageOperationError, LookupError)):
            raise StorageLookupError("lookup error")

    def test_exception_mro(self):
        """Test Method Resolution Order (MRO) for exceptions with multiple inheritance."""
        # StorageKeyError MRO should include both StorageError and KeyError
        mro = StorageKeyError.__mro__
        assert StorageError in mro
        assert KeyError in mro

        # StorageLookupError MRO should include StorageOperationError and LookupError
        mro = StorageLookupError.__mro__
        assert StorageOperationError in mro
        assert LookupError in mro
