"""Passthrough codec adapter - no transformation."""

from __future__ import annotations

from typing import TYPE_CHECKING

from ..protocols import ValueCodecProtocol
from .types import PassthroughEncoded, PassthroughSupportedValues


__all__ = ["PassthroughCodec"]


class PassthroughCodec:
    """
    Codec that performs no transformation on data.

    This adapter is suitable for in-memory storage where serialization
    is not required. It passes values through without any encoding or
    decoding overhead.

    Type Parameters:
        PassthroughValue: Any Python value
        PassthroughEncoded: Same as PassthroughValue (no transformation)
    """

    __slots__ = ("encode", "decode")

    def __init__(self) -> None:
        """Initialize passthrough codec with identity function references."""
        self.encode = lambda x: x  # type: ignore[return-value]
        self.decode = lambda x: x  # type: ignore[return-value]

    def encode(self, value: PassthroughSupportedValues) -> PassthroughEncoded:
        """Encode a supported value (no transformation)."""
        ...

    def decode(self, encoded: PassthroughEncoded) -> PassthroughSupportedValues:
        """Decode a supported value (no transformation)."""
        ...


if TYPE_CHECKING:
    _: type[ValueCodecProtocol[PassthroughSupportedValues, PassthroughEncoded]] = PassthroughCodec
