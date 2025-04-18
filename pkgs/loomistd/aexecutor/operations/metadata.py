from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class OperationMetadata:
    """
    Metadata for operations, used for introspection and visualization.

    Attributes:
        name: The name of the operation type
        description: A human-readable description of the operation
        custom_properties: Additional operation-specific metadata
    """

    name: str
    description: str
    custom_properties: dict[str, Any]

    def with_properties(self, **properties: dict[str, Any]) -> "OperationMetadata":
        """
        Create a new OperationMetadata with additional properties.

        Args:
            **properties: Additional properties to add

        Returns:
            A new OperationMetadata instance with the additional properties
        """
        return OperationMetadata(
            name=self.name,
            description=self.description,
            custom_properties={
                **self.custom_properties,
                **properties,
            },
        )
