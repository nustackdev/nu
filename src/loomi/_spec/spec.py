"""
Specification system for defining service/app properties and identity.
Note: temporary solution until we have a more robust system in place.
"""

from __future__ import annotations

import json
from base64 import b64encode
from functools import cached_property
from pathlib import Path
from typing import Any, Dict, Hashable, final

from pydantic import BaseModel, ConfigDict, Field

from .exceptions import SpecError

__all__ = ["Spec", "SpecField"]

SpecField = Field


class Spec(BaseModel, Hashable):
    """
    Temporary specification class for defining service/app properties and identity.
    Should be replaced with a more ergonomic and robust system in the future.

    This class is used to define the properties of a service or app, including its name,
    factory, and any additional fields.
    """

    model_config = ConfigDict(
        arbitrary_types_allowed=True,
        extra="allow",
        from_attributes=True,
        frozen=True,
    )

    name: str = Field(default="")
    factory: type

    def _serialize_value(self, value: Any) -> Any:
        if value is None:
            return None
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
