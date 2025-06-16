from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class ExpressionMetadata:
    """
    Metadata for expressions, used for introspection and visualization.

    Attributes:
        name: The name of the expression type
        description: A human-readable description of the expression
        custom_properties: Additional expression-specific metadata
    """

    name: str
    description: str
    custom_properties: dict[str, Any]

    def with_properties(self, **properties: dict[str, Any]) -> "ExpressionMetadata":
        """
        Create a new ExpressionMetadata with additional properties.

        Args:
            **properties: Additional properties to add

        Returns:
            A new ExpressionMetadata instance with the additional properties
        """
        return ExpressionMetadata(
            name=self.name,
            description=self.description,
            custom_properties={
                **self.custom_properties,
                **properties,
            },
        )
