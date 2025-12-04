"""Passthrough codec adapter - no transformation."""

from __future__ import annotations

from typing import TYPE_CHECKING


if TYPE_CHECKING:
    from everyshape.storage import ValueCodecProtocol
    from everyshape.types import Value

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

    def encode(self, value: Value) -> object:
        """Encode a supported value (no transformation)."""
        ...

    def decode(self, encoded: object) -> Value:
        """Decode a supported value (no transformation)."""
        ...


if TYPE_CHECKING:
    _: type[ValueCodecProtocol[object]] = PassthroughCodec
