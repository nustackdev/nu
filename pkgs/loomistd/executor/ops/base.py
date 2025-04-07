from __future__ import annotations

from typing import Any, Dict, List, Optional

from ..meta import OperationMetadata
from .protocol import Operation


class BaseOperation:
    """
    Base implementation of the Operation protocol.

    Provides common functionality for all operations.
    """

    def __init__(self, metadata: Optional[Dict[str, Any]] = None):
        """
        Initialize the operation with optional metadata.

        Args:
            metadata: Custom metadata for the operation
        """
        self._metadata = OperationMetadata(
            operation_type=self.__class__.__name__,
            description=self.__class__.__doc__,
            custom_metadata=metadata or {},
        )

    @property
    def metadata(self) -> OperationMetadata:
        """Get the operation's metadata."""
        return self._metadata

    def get_children(self) -> List["Operation"]:
        """
        Get all child operations of this operation.
        Default implementation returns an empty list.
        """
        return []
