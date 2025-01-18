"""Service spec system."""

from __future__ import annotations

import json
from base64 import b64encode
from typing import TYPE_CHECKING, final

from pydantic import BaseModel, Field, field_serializer

from .exceptions import SpecError
from .types import ServiceKey

if TYPE_CHECKING:
    from .base import BaseService


# This is a base class for all service specs
class Spec(BaseModel):
    """
    Base spec for all services.

    Attributes:
        name: Service name
        instance_id: Optional unique instance identifier
        factory: Optional custom factory class
    """

    class Config:
        orm_mode = True
        validate_assignment = True
        extra = "allow"  # Allow or prevent extra attributes
        arbitrary_types_allowed = True

    name: str = Field(default="")
    factory: type | None = Field(
        default=None
    )  # should be type[BaseService], avoiding circular import

    @classmethod
    def identity_fields(cls) -> set[str] | None:
        """Fields affecting instance identity."""
        if cls is Spec:
            return None
        raise NotImplementedError(f"identity_fields not implemented for {cls.__name__}")

    @classmethod
    def default_identity_fields(cls) -> set[str] | None:
        """Default identity fields."""
        return {"factory", "name"}

    @field_serializer("factory")
    def serialize_factory(self, factory: "type[BaseService]") -> str:
        return factory.factory_name() if factory is not None else "None"

    @final
    def identity(self) -> dict:
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
        """Generate stable hash key for deduplication."""
        if self.factory is None:
            raise SpecError("Factory is not defined")

        # Get identity fields
        identity_dict = self.identity()

        # Generate stable key
        sorted_items = json.dumps(identity_dict, sort_keys=True)
        key = b64encode(sorted_items.encode()).decode()

        return ServiceKey(key)
