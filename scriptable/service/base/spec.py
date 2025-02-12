"""
Service specification system for defining service properties and identity.

This module provides the Spec class which serves as the foundation for
defining service instances. It handles:
- Basic service properties like name and factory
- Identity field management for instance deduplication
- Key generation for unique instance identification
- Serialization of complex types like factory classes

The specification system is extensible through subclassing while maintaining
consistent identity and key generation behavior.
"""

from __future__ import annotations

import json
from base64 import b64encode
from typing import TYPE_CHECKING, final

from pydantic import BaseModel, Field, field_serializer

from .exceptions import SpecError
from .types import ServiceKey

if TYPE_CHECKING:
    from .bases import Service

__all__ = [
    "Spec",
]


class Spec(BaseModel):
    """
    Base specification class for all services.

    This class defines the core properties and behavior for service specifications.
    It handles identity management, key generation, and factory configuration
    while supporting extension through subclassing.

    Attributes:
        name (str): Service instance name, defaults to empty string
        factory (type | None): Service factory class, optional

    Class Configuration:
        - Supports ORM mode
        - Validates attribute assignments
        - Allows extra attributes
        - Supports arbitrary types

    Notes:
        - Subclasses must implement identity_fields() if they add fields
          affecting instance identity
        - Key generation is final and cannot be overridden
    """

    class Config:
        arbitrary_types_allowed = True
        extra = "allow"
        from_attributes = True
        frozen = True

    name: str = Field(default="")
    factory: type | None = Field(default=None)

    @classmethod
    def identity_fields(cls) -> set[str] | None:
        """
        Get fields that affect instance identity for this spec type.

        Returns:
            set[str] | None: Set of field names or None for base class

        Raises:
            NotImplementedError: Must be implemented by subclasses

        Notes:
            - Base Spec returns None
            - Subclasses must implement to define their identity fields
        """
        if cls is Spec:
            return None
        raise NotImplementedError(f"identity_fields not implemented for {cls.__name__}")

    @classmethod
    def default_identity_fields(cls) -> set[str] | None:
        """
        Get the default set of identity-affecting fields.

        Returns:
            set[str] | None: Set containing 'factory' and 'name'
        """
        return {"factory", "name"}

    @field_serializer("factory")
    def serialize_factory(self, factory: "type[Service]") -> str:
        """
        Serialize factory class to string representation.

        Args:
            factory: Service factory class

        Returns:
            str: String representation of factory or 'None'
        """
        return factory.factory_name() if factory is not None else "None"

    @final
    def identity(self) -> dict:
        """
        Generate identity dictionary for key generation.

        Returns:
            dict: Combined identity fields from default and class-specific sets

        Notes:
            - Combines default and class-specific identity fields
            - Handles nested specs recursively
            - Method is final and cannot be overridden
        """
        result = {}
        identity_fields = (self.default_identity_fields() or set()) | (
            self.identity_fields() or set()
        )
        model_dict = self.model_dump(include=identity_fields)

        for field, value in model_dict.items():
            if isinstance(value, Spec):
                result[field] = value.identity()
            else:
                result[field] = value

        return result

    @final
    @property
    def key(self) -> ServiceKey:
        """
        Generate unique key for service instance deduplication.

        Returns:
            ServiceKey: Unique identifier based on identity fields

        Raises:
            SpecError: If factory is not defined

        Notes:
            - Uses JSON serialization for stable dictionary representation
            - Encodes result in base64 for clean string format
            - Method is final and cannot be overridden
        """
        if self.factory is None:
            raise SpecError("Factory is not defined")

        identity_dict = self.identity()
        sorted_items = json.dumps(identity_dict, sort_keys=True)
        key = b64encode(sorted_items.encode()).decode()

        return ServiceKey(key)


__all__ = [
    "Spec",
]
