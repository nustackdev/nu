from __future__ import annotations

from typing import Protocol

from loomi.tree import StorageProtocol
from loomistd.codec import CodecProtocol

from ._types import StorageEncodedKeyT, StorageEncodedValueT, StorageKeyT, ValueT


__all__ = [
    "StorageServiceProtocol",
]


class StorageServiceProtocol(
    StorageProtocol[ValueT],
    Protocol[StorageKeyT, ValueT, StorageEncodedKeyT, StorageEncodedValueT],
):
    """Protocol defining state storage operations.

    Storage implementations handle the persistence of state data with:
    - Transactional guarantees
    - Proper error handling
    - Resource management
    - Type safety

    Type Parameters:
        KeyT: Key type (must be tuple of strings)
        ValueT: Value type (must be valid state value)
        EncodedKeyT: Encoded key type for storage
        EncodedValueT: Encoded value type for storage

    Implementation Requirements:
        - Must maintain ACID guarantees
        - Must handle concurrent access
        - Must validate all inputs
        - Must properly encode/decode data
    """

    @property
    def codec(
        self,
    ) -> CodecProtocol[StorageKeyT, ValueT, StorageEncodedKeyT, StorageEncodedValueT]:
        """Get codec for encoding/decoding keys and values.

        Returns:
            Codec instance
        """
        ...

    def connect(self) -> None:
        """Establish connection to storage backend.

        This method must:
        - Initialize resources
        - Verify backend health
        - Set up any required structures

        Raises:
            StorageConnectionError: If connection fails
        """
        ...

    def disconnect(self) -> None:
        """Close connection to storage backend.

        This method must:
        - Clean up resources
        - Flush pending changes
        - Handle existing transactions

        Raises:
            StorageConnectionError: If disconnection fails
        """
        ...
