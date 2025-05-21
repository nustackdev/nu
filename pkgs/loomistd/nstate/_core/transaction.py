"""
Transaction management for the state management system.

This module provides transaction handling capabilities through context managers.
It defines two primary classes:
- TransactionContext: A standalone context manager that returns a transaction object
- TransactionalBase: A mixin class for adding transaction capabilities to other classes

Both classes handle the transaction lifecycle (begin, commit, rollback) and provide
appropriate cleanup. They utilize a common base class to eliminate code duplication
while maintaining distinct behaviors.

Typical usage:
    # Standalone context manager
    with TransactionContext(backend) as tx:
        tx.set("key", "value")

    # As a mixin in a class
    class MyState(TransactionalBase["MyState"]):
        def __init__(self, backend):
            super().__init__()
            self._backend = backend

        @property
        def backend(self):
            return self._backend

    # Using the class with transaction capabilities
    with MyState(backend) as state:
        state.do_something()  # Uses state.tx internally
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from types import TracebackType
from typing import Generic, Optional, TypeVar, cast

from .._state.backend import ObservableKVBackend, ObservableKVTransaction

__all__ = ["TransactionContext", "TransactionalBase"]

# Type variables
T = TypeVar("T")  # For the return type of __enter__
TSelf = TypeVar("TSelf", bound="TransactionalBase")  # For self-referential types


class BaseTransactionHandler(Generic[T], ABC):
    """
    Abstract base class for transaction handling.

    This class provides common transaction lifecycle management functionality
    including beginning transactions, committing successful operations, and
    rolling back failed operations. It uses the template method pattern to allow
    subclasses to customize specific behaviors while sharing common implementation.

    The class is generic, allowing subclasses to specify what type is returned
    from the __enter__ method when used as a context manager.

    Attributes:
        _tx: The current transaction object or None if no transaction is active
        _created_tx: Flag indicating whether this handler created the transaction
                     (used to determine if it should be committed/rolled back)
    """

    def __init__(self) -> None:
        """
        Initialize the base transaction handler.

        Sets up the initial state with no active transaction.
        """
        self._tx: Optional[ObservableKVTransaction] = None
        self._created_tx: bool = False

    @abstractmethod
    def _get_backend(self) -> ObservableKVBackend:
        """
        Get the backend storage interface.

        This abstract method must be implemented by subclasses to provide
        access to the storage backend that will be used for transaction operations.

        Returns:
            ObservableKVBackend: The backend storage interface to use for transactions
        """
        pass

    @abstractmethod
    def _get_enter_result(self) -> T:
        """
        Get the result to return from __enter__.

        This abstract method must be implemented by subclasses to determine
        what object should be returned when entering the context manager.
        This allows different subclasses to return either the transaction
        object itself or the containing object (self).

        Returns:
            T: The object to be returned from __enter__
        """
        pass

    def __enter__(self) -> T:
        """
        Enter the context and handle transaction creation.

        If no transaction exists, creates a new one using the backend provided
        by _get_backend(). Otherwise, reuses the existing transaction.

        The method delegates to _get_enter_result() to determine what to return,
        allowing subclasses to customize the return value.

        Returns:
            The result of _get_enter_result(), which depends on the subclass

        Example:
            ```python
            # For TransactionContext, returns the transaction
            with TransactionContext(backend) as tx:
                tx.set("key", "value")

            # For TransactionalBase, returns self
            with MyState(backend) as state:
                state.do_something()
            ```
        """
        if self._tx is None:
            # Create a new transaction
            self._tx = self._get_backend().begin_transaction()
            self._created_tx = True

        return self._get_enter_result()

    def __exit__(
        self,
        exc_type: Optional[type[BaseException]],
        exc_val: Optional[BaseException],
        exc_tb: Optional[TracebackType],
    ) -> bool:
        """
        Exit context manager, handling transaction commit or rollback.

        This method is called when exiting the context manager block ('with' statement).
        It handles the transaction lifecycle:
        - If an exception occurred, the transaction is rolled back
        - If no exception occurred, the transaction is committed
        - Regardless of outcome, the transaction reference is cleared

        The method only takes action if this handler created the transaction
        (indicated by self._created_tx). This allows for nested transaction contexts.

        Args:
            exc_type: Exception type, if an exception was raised
            exc_val: Exception value, if an exception was raised
            exc_tb: Exception traceback, if an exception was raised

        Returns:
            bool: Always False, to propagate exceptions rather than suppressing them

        Example:
            ```python
            try:
                with TransactionContext(backend) as tx:
                    tx.set("key", "value")
                    raise ValueError("An error")
                # Transaction will be rolled back automatically
            except ValueError:
                # Handle the error
                pass
            ```
        """
        if not self._created_tx or self._tx is None:
            return False

        try:
            if exc_type is not None:
                # Exception occurred, rollback
                self._tx.rollback()
            else:
                # No exception, commit
                self._tx.commit()
        finally:
            # Clear transaction references
            self._tx = None
            self._created_tx = False
        return False  # Don't suppress exceptions


class TransactionContext(BaseTransactionHandler[ObservableKVTransaction]):
    """
    Transaction manager for state operations.

    This class provides a standalone context manager for transaction handling,
    returning the transaction object itself when used in a 'with' statement.
    It is designed for direct transaction operations when you need the raw
    transaction object.

    Attributes:
        _backend: The backend storage interface used for transactions
        _tx: The current transaction object or None if no transaction is active
        _created_tx: Flag indicating whether this handler created the transaction

    Example usage:
        ```python
        with TransactionContext(backend) as tx:
            # Use tx directly for operations
            tx.set("key", "value")
            value = tx.get("key")
        # Transaction automatically committed on exit
        ```
    """

    def __init__(
        self,
        backend: ObservableKVBackend,
        *,
        tx: Optional[ObservableKVTransaction] = None,
    ) -> None:
        """
        Initialize the transaction manager.

        Creates a transaction context that will use the provided backend.
        Optionally accepts an existing transaction to use instead of creating
        a new one when entering the context.

        Args:
            backend: Backend storage interface to use for transactions
            tx: Optional transaction to use instead of creating a new one

        Example:
            ```python
            # Standard usage with a new transaction
            context = TransactionContext(backend)

            # Reusing an existing transaction
            existing_tx = backend.begin_transaction()
            context = TransactionContext(backend, tx=existing_tx)
            ```
        """
        super().__init__()
        self._backend = backend
        self._tx = tx  # Override the None from the base class

    def _get_backend(self) -> ObservableKVBackend:
        """
        Get the backend storage interface.

        Implementation of the abstract method from BaseTransactionHandler.
        Returns the backend provided during initialization.

        Returns:
            ObservableKVBackend: The backend storage interface
        """
        return self._backend

    def _get_enter_result(self) -> ObservableKVTransaction:
        """
        Return the transaction when entering the context.

        Implementation of the abstract method from BaseTransactionHandler.
        Returns the current transaction object (self._tx), which is guaranteed
        to be non-None at this point due to the logic in __enter__.

        Returns:
            ObservableKVTransaction: The current transaction object
        """
        return cast(ObservableKVTransaction, self._tx)  # At this point, self._tx is never None


class TransactionalBase(BaseTransactionHandler[TSelf], ABC):
    """
    Mixin class for adding transaction capabilities to other classes.

    This class provides context manager functionality that returns the object itself
    (rather than the transaction) when used in a 'with' statement. This allows for
    a more natural API when transaction handling is part of a larger object's behavior.

    Subclasses must implement the 'backend' property to provide access to the
    backend storage interface.

    Attributes:
        _tx: The current transaction object or None if no transaction is active
        _created_tx: Flag indicating whether this handler created the transaction

    Example:
        ```python
        class State(TransactionalBase["State"]):
            def __init__(self, backend):
                super().__init__()
                self._backend = backend

            @property
            def backend(self):
                return self._backend

            def update_value(self, key, value):
                if self.tx:
                    self.tx.set(key, value)
                else:
                    with self as state:
                        state.tx.set(key, value)

        # Using the class with transaction capabilities
        state = State(backend)
        with state as s:
            s.update_value("key1", "value1")
            s.update_value("key2", "value2")
        # Transaction automatically committed on exit
        ```
    """

    def __init__(self) -> None:
        """
        Initialize the mixin.

        Sets up the initial transaction state. Note that unlike TransactionContext,
        this class doesn't take a backend in the constructor, as it's expected to
        be provided by the subclass through the 'backend' property.

        Note: The backend should be set by the inheriting class.
        """
        super().__init__()

    def _get_backend(self) -> ObservableKVBackend:
        """
        Get the backend storage interface.

        Implementation of the abstract method from BaseTransactionHandler.
        Delegates to the 'backend' property, which must be implemented by subclasses.

        Returns:
            ObservableKVBackend: The backend storage interface

        Raises:
            NotImplementedError: If the subclass hasn't implemented the backend property
        """
        return self.backend

    def _get_enter_result(self) -> TSelf:
        """
        Return self when entering the context.

        Implementation of the abstract method from BaseTransactionHandler.
        Returns the object itself rather than the transaction, allowing for
        method chaining and a more natural API in subclasses.

        Returns:
            The object itself (self)
        """
        return cast(TSelf, self)

    @property
    def tx(self) -> Optional[ObservableKVTransaction]:
        """
        Get the current transaction.

        Provides access to the active transaction if one exists. This is the
        primary way for subclasses to access the transaction for operations.

        Returns:
            Optional[ObservableKVTransaction]: Current transaction or None if no transaction is active

        Example:
            ```python
            class MyState(TransactionalBase["MyState"]):
                # ...implementation...

                def set_value(self, key, value):
                    if self.tx:
                        self.tx.set(key, value)
                    else:
                        # Create a transaction if one doesn't exist
                        with self:
                            self.tx.set(key, value)
            ```
        """
        return self._tx

    @property
    @abstractmethod
    def backend(self) -> ObservableKVBackend:
        """
        Get the backend storage interface.

        This abstract property must be implemented by subclasses to provide
        access to the storage backend that will be used for transaction operations.

        Returns:
            ObservableKVBackend: Backend storage interface

        Example implementation:
            ```python
            class MyState(TransactionalBase["MyState"]):
                def __init__(self, backend):
                    super().__init__()
                    self._backend = backend

                @property
                def backend(self):
                    return self._backend
            ```
        """
        pass
