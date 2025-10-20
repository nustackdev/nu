"""View protocol definitions.

Protocols define the capabilities that views must provide for different
access patterns.

Design Philosophy:
    - Protocols as contracts (not inheritance hierarchies)
    - Structural typing (duck typing with type safety)
    - No runtime checks (trust static analysis)
    - Composable (views can implement multiple protocols)

Protocol Extension Pattern:
    To add new protocol (e.g., SequenceProtocol):
    1. Define protocol with required methods
    2. Document which views implement it
    3. No registration needed - structural typing

Example:
    class DictView:  # Implements MutableMappingProtocol
        def get(self, key: str) -> Any: ...
        def set(self, key: str, value: Any) -> None: ...
        def remove(self, key: str) -> None: ...
        def keys(self) -> list[str]: ...
        def __contains__(self, key: str) -> bool: ...

    # Type checker verifies DictView has all required methods
    view: MutableMappingProtocol = DictView(node, ctx)  ✓
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Protocol


if TYPE_CHECKING:
    from .types import KeyComponent, Value

__all__ = [
    "MappingProtocol",
    "MutableMappingProtocol",
]

# ============================================================================
# Mapping Protocol
# ============================================================================


class MappingProtocol(Protocol):
    """Protocol for mapping-like views (key → value).

    Views implementing this protocol support:
    - Read access via get(key)
    - Key existence checking
    - Key enumeration

    Used by: DictView, any custom mapping views
    """

    def get(self, key: KeyComponent) -> Value:
        """Retrieve value by key.

        Args:
            key: String key to look up

        Returns:
            Value at key, or None if not found
        """
        ...

    def keys(self) -> list[KeyComponent]:
        """Return all keys in the mapping.

        Returns:
            List of string keys
        """
        ...

    def __contains__(self, key: KeyComponent) -> bool:
        """Check if key exists in mapping.

        Args:
            key: Key to check

        Returns:
            True if key exists
        """
        ...


class MutableMappingProtocol(MappingProtocol, Protocol):
    """Protocol for mutable mapping-like views.

    Extends MappingProtocol with mutation operations.

    Used by: DictView in write contexts
    """

    def set(self, key: KeyComponent, value: Value) -> None:
        """Set value at key.

        Args:
            key: String key
            value: Value to store
        """
        ...

    def remove(self, key: KeyComponent) -> None:
        """Remove key from mapping.

        Args:
            key: Key to remove
        """
        ...


__all__ = [
    "MappingProtocol",
    "MutableMappingProtocol",
]
