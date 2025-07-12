"""
Resource Spec Module

This implements a high-performance, type-safe spec system for Loomi with:
- attrs for frozen structs
- SHA-256 content-based hashing for deterministic keys
- Cached computations for performance
- Fluent transformation API
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any, Dict, Self, Type

import attrs

__all__ = [
    "BaseSpec",
]


@attrs.define(frozen=True, slots=True, kw_only=True)
class BaseSpec:
    """
    Base immutable specification with high-performance hashing.

    Features:
    - Frozen attrs structs for immutability
    - Content-based SHA-256 hashing for deterministic keys
    - Cached properties for performance
    - Fluent transformation API
    - Rich comparison support
    """

    @property
    def key(self) -> str:
        """
        Generate deterministic key using SHA-256 hashing.

        This is cached for performance since specs are immutable.
        """
        # Use JSON for consistent string encoding
        data = self._get_key_data()
        json_str = json.dumps(data, sort_keys=True, separators=(",", ":"))

        # SHA-256 for deterministic, collision-resistant keys
        hasher = hashlib.sha256()
        hasher.update(json_str.encode("utf-8"))

        # Add optional prefix for namespacing
        return f"{hasher.hexdigest()}"

    def _get_key_data(self) -> Dict[str, Any]:
        """Get data for key generation, excluding specified fields."""
        data: Dict[str, Any] = {}

        for field in attrs.fields(self.__class__):
            value = getattr(self, field.name)
            data[field.name] = self._serialize_value(value)

        return data

    def _serialize_value(self, value: Any) -> Any:
        """Serialize a value for consistent hashing."""
        if value is None:
            return None
        elif isinstance(value, BaseSpec):
            # Recursive spec serialization
            return {"__spec__": value.key}
        elif isinstance(value, type):
            return self._serialize_type(value)
        elif callable(value) and hasattr(value, "__module__") and hasattr(value, "__qualname__"):
            # Serialize callables by module + qualname
            return f"{value.__module__}:{value.__qualname__}"
        elif isinstance(value, (list, tuple)):
            return [self._serialize_value(item) for item in value]
        elif isinstance(value, dict):
            return {str(k): self._serialize_value(v) for k, v in sorted(value.items())}
        else:
            # FIXME: Generic object serialization
            # Currently supports basic common types and returns value directly if not recognized
            if isinstance(value, Path):
                return str(value)
            return value

    def _serialize_type(self, typ: Type) -> str:
        """Serialize a type reference consistently."""
        if hasattr(typ, "__module__") and hasattr(typ, "__qualname__"):
            return f"{typ.__module__}:{typ.__qualname__}"
        return typ.__name__

    def __hash__(self) -> int:
        """Use the cached key for hashing."""
        return hash(self.key)

    def __eq__(self, other: Any) -> bool:
        """Specs are equal if they have the same key."""
        if not isinstance(other, BaseSpec):
            return False
        return self.key == other.key

    # Manipulation API

    def with_value_at(self, path: str, /, *paths: str, value: Any) -> Self:
        """
        Update the value at the specified path, creating a new spec instance.

        Traverses the existing spec structure and creates a new spec with the
        modified value at the specified path.

        Args:
            path: First path segment
            *paths: Additional path segments
            value: The new value to set at the specified path

        Returns:
            New spec instance with the updated value

        Raises:
            ValueError: If the path cannot be navigated or the target is not a spec
        """
        path_parts = (path,) + paths

        if len(path_parts) == 1:
            # Simple case - direct field update
            field_name = path_parts[0]
            if not any(field.name == field_name for field in attrs.fields(self.__class__)):
                raise ValueError(f"Field '{field_name}' not found in {self.__class__.__name__}")
            return attrs.evolve(self, **{field_name: value})

        # Complex case - nested path
        return self._evolve_nested_path(path_parts, value)

    def _evolve_nested_path(self, path_parts: tuple[str, ...], value: Any) -> Self:
        """
        Helper method to evolve a spec with a nested path update.

        Args:
            path_parts: Path segments to traverse
            value: Value to set at the final path segment

        Returns:
            New spec instance with the updated nested value

        Raises:
            ValueError: If the path cannot be navigated
        """
        current_key = path_parts[0]
        remaining_path = path_parts[1:]

        # Check if the current key exists
        if not any(field.name == current_key for field in attrs.fields(self.__class__)):
            raise ValueError(
                f"Cannot navigate path: '{current_key}' not found in {self.__class__.__name__}"
            )

        # Get the value at this level
        next_obj = getattr(self, current_key)

        # If None and we need to go deeper, that's an error
        if next_obj is None:
            raise ValueError(
                f"Cannot navigate path: '{current_key}' is None in {self.__class__.__name__} "
                f"but further path segments {remaining_path} require an object"
            )

        # If this isn't a BaseSpec object but we need to go deeper, that's an error
        if not isinstance(next_obj, BaseSpec):
            raise ValueError(
                f"Cannot navigate path: '{current_key}' in {self.__class__.__name__} "
                f"is {type(next_obj).__name__} which doesn't support nested paths"
            )

        # Recursively update the nested object
        updated_nested = next_obj.with_value_at(*remaining_path, value=value)

        # Return evolved instance with the updated nested object
        return attrs.evolve(self, **{current_key: updated_nested})
