"""MessagePack codec adapter - efficient binary serialization."""

from __future__ import annotations

from typing import TYPE_CHECKING


if TYPE_CHECKING:
    from redwood.abc import Value
    from redwood.backend import ValueCodecProtocol


try:
    import msgpack
except ImportError as e:
    raise ImportError(
        "msgpack is required for MessagePackCodec. Install via: pip install msgpack"
    ) from e


__all__ = ["MessagePackCodec"]


class MessagePackCodec:
    """Codec using MessagePack for efficient binary serialization.

    MessagePack is a binary serialization format that is more compact and
    faster than JSON while supporting similar data types. It is ideal for
    network transmission and persistent storage.

    Performance:
        - Encode/decode methods are direct function references for zero overhead
        - No method call indirection or wrapper overhead
    """

    def __init__(self) -> None:
        """Initialize MessagePack codec with direct function references.

        The encode and decode attributes are set to msgpack library functions
        directly to avoid any method call overhead.
        """
        self.encode = msgpack.packb  # type: ignore[return-value]
        self.decode = msgpack.unpackb  # type: ignore[return-value]

    def encode(self, value: Value) -> bytes:
        """Encode a supported value into MessagePack binary format."""
        ...

    def decode(self, encoded: bytes) -> Value:
        """Decode MessagePack binary data back into a supported value."""
        ...


if TYPE_CHECKING:
    _: type[ValueCodecProtocol[bytes]] = MessagePackCodec
