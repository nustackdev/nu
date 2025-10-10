"""Passthrough codec adapter - no transformation."""

from __future__ import annotations

from typing import TYPE_CHECKING

from redwood.protocols import ValueCodecProtocol
from redwood.types import Value

from .types import PassthroughEncoded


__all__ = ["PassthroughCodec"]


class PassthroughCodec:
    """Codec that performs no transformation on data.

    This adapter is suitable for in-memory storage where serialization
    is not required. It passes values through without any encoding or
    decoding overhead.

    Type Parameters:
        PassthroughValue: Any Python value
        PassthroughEncoded: Same as PassthroughValue (no transformation)
    """

    def __init__(self) -> None:
        """Initialize passthrough codec with identity function references."""
        self.encode = lambda x: x  # type: ignore[return-value]
        self.decode = lambda x: x  # type: ignore[return-value]

    def encode(self, value: Value) -> PassthroughEncoded:
        """Encode a supported value (no transformation)."""
        ...

    def decode(self, encoded: PassthroughEncoded) -> Value:
        """Decode a supported value (no transformation)."""
        ...


if TYPE_CHECKING:
    _: type[ValueCodecProtocol[PassthroughEncoded]] = PassthroughCodec
