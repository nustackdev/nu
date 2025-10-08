"""MessagePack codec adapter - efficient binary serialization."""

from __future__ import annotations

from collections.abc import Callable

from ..protocols import ValueCodecProtocol
from .types import MessagePackEncoded, MessagePackSupportedValues


try:
    import msgpack
except ImportError as e:
    msg = "msgpack is required for MessagePackCodec. Install via: pip install msgpack"
    raise ImportError(msg) from e


__all__ = ["MessagePackCodec"]


class MessagePackCodec(ValueCodecProtocol[MessagePackSupportedValues, MessagePackEncoded]):
    """
    Codec using MessagePack for efficient binary serialization.

    MessagePack is a binary serialization format that is more compact and
    faster than JSON while supporting similar data types. It is ideal for
    network transmission and persistent storage.

    Type Parameters:
        MessagePackValue: None, bytes, bool, int, float, str, list, or dict
        MessagePackEncoded: bytes (binary MessagePack format)

    Performance:
        - Encode/decode methods are direct function references for zero overhead
        - No method call indirection or wrapper overhead
    """

    __slots__ = ("encode", "decode")

    encode: Callable[[MessagePackSupportedValues], MessagePackEncoded]
    decode: Callable[[MessagePackEncoded], MessagePackSupportedValues]

    def __init__(self) -> None:
        """
        Initialize MessagePack codec with direct function references.

        The encode and decode attributes are set to msgpack library functions
        directly to avoid any method call overhead.
        """
        self.encode: Callable[[MessagePackSupportedValues], MessagePackEncoded] = msgpack.packb
        self.decode: Callable[[MessagePackEncoded], MessagePackSupportedValues] = msgpack.unpackb
