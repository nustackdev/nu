"""Passthrough codec adapter - no transformation."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any


if TYPE_CHECKING:
    from redwood.abc import Value
    from redwood.be import ValueCodecProtocol

__all__ = ["PassthroughCodec"]


class PassthroughCodec:
    """Codec that performs no transformation on data.

    This adapter is suitable for in-memory storage where serialization
    is not required. It passes values through without any encoding or
    decoding overhead.

    """

    def __init__(self) -> None:
        """Initialize passthrough codec with identity function references."""
        self.encode = lambda x: x  # type: ignore[return-value]
        self.decode = lambda x: x  # type: ignore[return-value]

    def encode(self, value: Value) -> Any:
        """Encode a supported value (no transformation)."""
        ...

    def decode(self, encoded: Any) -> Value:
        """Decode a supported value (no transformation)."""
        ...


if TYPE_CHECKING:
    _: type[ValueCodecProtocol[Any]] = PassthroughCodec
