"""
specification system for defining service/app properties and identity.

This module provides the Spec class which serves as the foundation for
defining instances. It handles:
- Basic properties like name and factory
- Identity field management for instance deduplication
- Key generation for unique instance identification
- Serialization of complex types like factory classes

The specification system is extensible through subclassing while maintaining
consistent identity and key generation behavior.
"""

from __future__ import annotations

import json
from base64 import b64encode
from functools import cached_property
from typing import final

from pydantic import BaseModel, Field, field_serializer

from .exceptions import SpecError

__all__ = [
    "Spec",
    "SpecField",
]

SpecField = Field


class Spec(BaseModel):
    """
    Base specification class for all apps and services.

    This class defines the core properties and behavior for service and app specifications.
    It handles identity management, key generation, and factory configuration
    while supporting extension through subclassing.

    Attributes:
        name (str): Instance name, defaults to empty string
        factory (type | None): Factory class

    Class Configuration:
        - Supports ORM mode
        - Validates attribute assignments
        - Allows extra attributes
        - Supports arbitrary types

    Notes:
        - Key generation is final and cannot be overridden
    """

    class Config:
        arbitrary_types_allowed = True
        extra = "allow"
        from_attributes = True
        frozen = True

    name: str = Field(default="")
    factory: type = Field()

    @field_serializer("factory")
    def serialize_factory(self, factory: type) -> str:
        """
        Serialize factory class to string representation.

        Args:
            factory: Service factory class

        Returns:
            str: String representation of factory or 'None'
        """
        return factory.factory_name() if hasattr(factory, "factory_name") else "None"

    @final
    @cached_property
    def key(self) -> str:
        """
        Generate unique key for instance deduplication.

        Returns:
            str: Unique identifier based on identity fields

        Raises:
            SpecError: If factory is not defined

        Notes:
            - Uses JSON serialization for stable dictionary representation
            - Encodes result in base64 for clean string format
            - Method is final and cannot be overridden
        """
        if self.factory is None:
            raise SpecError("Factory is not defined")

        identity_dict = self.model_dump(mode="json")
        sorted_items = json.dumps(identity_dict, sort_keys=True)
        key = b64encode(sorted_items.encode()).decode()

        return str(key)
