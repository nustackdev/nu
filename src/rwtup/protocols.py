"""Protocol definitions for key codec interfaces."""

from __future__ import annotations

from typing import Protocol

from .types import EncodedKeyT, Key


class KeyCodec(Protocol[EncodedKeyT]):
    """Protocol for key codecs that encode/decode tuples to preserve lexicographic ordering.

    Key codecs are responsible for converting tuple keys (containing strings and integers)
    into a format suitable for storage in key-value stores while maintaining sort order.
    """

    def encode(self, key: Key) -> EncodedKeyT:
        """Encode a tuple key into the target format.

        Args:
            key: Tuple containing strings and/or integers

        Returns:
            Encoded key in the target format

        Raises:
            EncodeError: If encoding fails due to invalid input or constraints
        """
        ...

    def decode(self, encoded: EncodedKeyT) -> Key:
        """Decode an encoded key back to the original tuple.

        Args:
            encoded: Previously encoded key

        Returns:
            Original tuple key

        Raises:
            DecodeError: If decoding fails due to invalid or corrupted data
        """
        ...


__all__ = [
    "KeyCodec",
    "EncodedKeyT",
]
