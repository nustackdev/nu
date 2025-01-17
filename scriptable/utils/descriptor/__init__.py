"""
Type-safe and validated descriptors for Python classes.

This module provides a flexible descriptor implementation with built-in type checking,
validation, and customizable storage strategies. It offers a clean way to define
class attributes with runtime type safety and validation rules.

Features:
    - Static type checking with generics support
    - Custom validation functions
    - Configurable storage strategies
    - Flexible validation failure handling
    - Optional value support
    - Comprehensive error reporting

Example:
    ```python
    from typing import Optional
    from descriptors import BaseDescriptor, ValueValidationError

    class StringDescriptor(BaseDescriptor[str]):
        def _validate_type(self, value: Any) -> str:
            if not isinstance(value, str):
                raise TypeValidationError(
                    "Value must be a string",
                    self._metadata.name,
                    value,
                    self._metadata.type,
                )
            return value

        def _get_default(self) -> str:
            return ""

    def String() -> str:
        return StringDescriptor()  # type: ignore
    ```

Storage Strategies:
    - WEAKREF (default): Stores values in a weakref dictionary to prevent memory leaks
    - INSTANCE_DICT: Stores values directly in instance __dict__

Validation Strategies:
    - STRICT: Raises exceptions on validation failures
    - LENIENT: Logs warnings/errors but allows invalid values

Notes:
    - Descriptors are type-bound using the Generic[T] pattern
    - Custom validators receive the validated value and should return bool
    - None values can be allowed/disallowed per descriptor
    - All descriptors must implement _validate_type() and _get_default()
"""

from .base import BaseDescriptor
from .exceptions import TypeValidationError, ValueValidationError
from .types import StorageStrategy, ValidationStrategy
