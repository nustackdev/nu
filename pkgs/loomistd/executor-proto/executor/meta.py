from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, Optional


@dataclass
class OperationMetadata:
    """
    Metadata about an operation.

    Contains information that describes an operation, used for
    introspection, visualization, and execution planning.
    """

    # The type of operation (e.g., "Function", "Sequence")
    operation_type: str

    # Human-readable description of the operation
    description: Optional[str] = None

    # Additional metadata specific to the operation type
    custom_metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert metadata to a dictionary.

        Useful for serialization and logging.

        Returns:
            Dictionary representation of the metadata
        """
        return {
            "type": self.operation_type,
            "description": self.description,
            **self.custom_metadata,
        }
