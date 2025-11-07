"""Scan protocol - Pythonic iteration interface."""

from __future__ import annotations

from typing import TYPE_CHECKING, Protocol, runtime_checkable


if TYPE_CHECKING:
    from collections.abc import Generator

    from redwood.abc import TupleKey, Value


@runtime_checkable
class ScanProtocol(Protocol):
    """Pythonic scan interface for range iteration.

    Provides dict-like iteration methods with configurable scan options.
    Designed to feel natural and Pythonic for common iteration patterns.

    Examples:
        # Direct iteration yields (key, value) tuples
        for key, value in tx.scan(options):
            process(key, value)

        # Explicit items iteration
        for key, value in tx.scan(options).items():
            process(key, value)

        # Keys only
        for key in tx.scan(options).keys():
            process(key)

        # Values only
        for value in tx.scan(options).values():
            process(value)

        # Reverse iteration
        for key, value in reversed(tx.scan(options)):
            process(key, value)

        # Context manager for explicit cleanup
        with tx.scan(options) as scan:
            for key, value in scan:
                process(key, value)
    """

    def items(self) -> Generator[tuple[TupleKey, Value], None, None]:
        """Iterate over (key, value) tuples.

        Yields:
            Tuples of (key, value) for each item in scan range.

        Raises:
            StorageOperationError: If iteration fails.
        """
        ...

    def keys(self) -> Generator[TupleKey, None, None]:
        """Iterate over keys only.

        Yields:
            Keys in scan range.

        Raises:
            StorageOperationError: If iteration fails.
        """
        ...

    def values(self) -> Generator[Value, None, None]:
        """Iterate over values only.

        Yields:
            Values in scan range.

        Raises:
            StorageOperationError: If iteration fails.
        """
        ...
