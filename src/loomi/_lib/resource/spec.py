"""
Specification system for defining resource/app properties and identity.
Note: temporary solution until we have a more robust system in place.
"""

from __future__ import annotations

import json
from base64 import b64encode
from functools import cached_property
from pathlib import Path
from typing import Any, Dict, Hashable, Self, final

from pydantic import BaseModel, ConfigDict, Field, PrivateAttr

from .exceptions import SpecError

__all__ = ["Spec", "SpecField"]

SpecField = Field


class Spec(BaseModel, Hashable):
    """
    Temporary specification class for defining resource/app properties and identity.
    Should be replaced with a more ergonomic and robust system in the future.

    This class is used to define the properties of a resource or app, including its name,
    factory, and any additional fields.
    """

    model_config = ConfigDict(
        arbitrary_types_allowed=True,
        extra="allow",
        from_attributes=True,
        frozen=False,
        validate_assignment=True,
        validate_default=True,
    )

    name: str = Field(default="")
    factory: type

    _is_remote: bool = PrivateAttr(default=False)
    _remote_client_spec: Spec | None = PrivateAttr(default=None)

    def with_value_at(self, path: str, /, *paths: str, value: Any) -> Self:
        """
        Update the value at the specified path directly.

        Traverses the existing spec structure and modifies values in place.

        Args:
            path: First path segment
            *paths: Additional path segment
            value: The new value to set at the specified path

        Returns:
            Self for method chaining
        """
        # Use a helper method to keep the code clean
        self._set_nested_value(self, (path,) + paths, value)
        return self

    def _set_nested_value(self, obj: Spec, path_parts: tuple[str, ...], value: Any) -> None:
        """
        Helper method to set a value at a nested path.

        Args:
            obj: Current object being traversed
            path_parts: Remaining path segments
            value: Value to set at the final path segment
        """
        if len(path_parts) == 1:
            # We're at the final level - set the attribute directly
            final_key = path_parts[0]

            # Set the attribute - Pydantic will validate the type
            setattr(obj, final_key, value)

            return

        # We need to navigate deeper
        current_key = path_parts[0]
        remaining_path = path_parts[1:]

        # Check if the current key exists
        if not hasattr(obj, current_key):
            raise ValueError(
                f"Cannot navigate path: '{current_key}' not found in {obj.__class__.__name__}"
            )

        # Get the value at this level
        next_obj = getattr(obj, current_key)

        # If None and we need to go deeper, that's an error
        if next_obj is None:
            raise ValueError(
                f"Cannot navigate path: '{current_key}' is None in {obj.__class__.__name__} "
                f"but further path segments {remaining_path} require an object"
            )

        # If this isn't a Spec object but we need to go deeper, that's an error
        if not isinstance(next_obj, Spec):
            raise ValueError(
                f"Cannot navigate path: '{current_key}' in {obj.__class__.__name__} "
                f"is {type(next_obj).__name__} which doesn't support nested paths"
            )

        # Continue traversing
        self._set_nested_value(next_obj, remaining_path, value)

    def _serialize_value(self, value: Any) -> Any:
        if value is None:
            return None
        elif callable(value) and hasattr(value, "__module__") and hasattr(value, "__name__"):
            # Handle function serialization
            return f"{value.__module__}.{value.__name__}"
        elif isinstance(value, Spec):
            return value._dump()
        elif isinstance(value, Path):
            return str(value)
        elif isinstance(value, type):
            return value.factory_name() if hasattr(value, "factory_name") else value.__name__
        elif isinstance(value, list):
            return [self._serialize_value(item) for item in value]
        elif isinstance(value, dict):
            return {str(k): self._serialize_value(v) for k, v in value.items()}
        else:
            return value

    def _dump(self) -> Dict[str, Any]:
        result = {}

        # Process model fields
        for field_name in self.model_fields:
            if hasattr(self, field_name):
                result[field_name] = self._serialize_value(getattr(self, field_name))

        # Process extra fields
        for field_name, value in self.__dict__.items():
            if field_name not in result and not field_name.startswith("_"):
                result[field_name] = self._serialize_value(value)

        return result

    @final
    @cached_property
    def key(self) -> str:
        if self.factory is None:
            raise SpecError("Factory is not defined")

        identity_dict = self._dump()
        sorted_items = json.dumps(identity_dict, sort_keys=True)
        key = b64encode(sorted_items.encode()).decode()

        return str(key)

    def __hash__(self) -> int:
        return hash(self.key)

    def __eq__(self, other):
        if not isinstance(other, Spec):
            return False
        return self.key == other.key

    def is_remote(self) -> bool:
        """
        Check if the spec is a remote spec.
        """
        return self._is_remote

    def as_remote(self, client_spec: Spec) -> Self:
        """
        Convert the spec to a remote spec.
        """
        if not isinstance(client_spec, Spec):
            raise SpecError("Client spec must be an instance of Spec")

        # Create a new spec with the same properties but for remote use
        self._is_remote = True
        self._remote_client_spec = client_spec

        return self

    def get_local_spec(self) -> Self:
        """
        Get the local spec without remote properties.
        """
        if self._is_remote:
            # Create a copy without remote properties
            local_spec = self.model_dump(exclude={"_is_remote", "_remote_client_spec"})
            return self.__class__(**local_spec)
        return self

    def get_remote_spec(self) -> Spec:
        """
        Get the remote spec with client properties.
        """
        if not self._is_remote or self._remote_client_spec is None:
            raise SpecError("This spec is not a remote spec")

        return self._remote_client_spec
