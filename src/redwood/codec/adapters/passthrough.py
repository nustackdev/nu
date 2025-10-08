"""Passthrough codec adapter - no transformation."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from ..protocols import ValueCodecProtocol
from .types import PassthroughEncoded, PassthroughSupportedValues


__all__ = ["PassthroughCodec"]


class PassthroughCodec(ValueCodecProtocol[PassthroughSupportedValues, PassthroughEncoded]):
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

    encode: Callable[[PassthroughSupportedValues], PassthroughEncoded]
    decode: Callable[[PassthroughEncoded], PassthroughSupportedValues]

    def __init__(self) -> None:
        """Initialize passthrough codec with identity function references."""
        self.encode: Callable[[PassthroughSupportedValues], PassthroughEncoded] = self._identity
        self.decode: Callable[[PassthroughEncoded], PassthroughSupportedValues] = self._identity

    @staticmethod
    def _identity(value: Any) -> Any:
        """
        Identity function that returns the input unchanged.

        Args:
            value: Any value to pass through

        Returns:
            The same value without modification
        """
        return value
