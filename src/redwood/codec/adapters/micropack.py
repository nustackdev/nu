"""MicroPack codec adapter - optimized binary serialization."""

from __future__ import annotations

from collections.abc import Callable

from ..protocols import ValueCodecProtocol
from .types import MicroPackEncoded, MicroPackSupportedValues


try:
    from micropack import Codec
except ImportError as e:
    msg = "micropack is required for MicroPackCodec. Install via: pip install micropack"
    raise ImportError(msg) from e


__all__ = ["MicroPackCodec"]


class MicroPackCodec(ValueCodecProtocol[MicroPackSupportedValues, MicroPackEncoded]):
    """
    Codec using MicroPack for optimized binary serialization.

    MicroPack provides high-performance binary serialization with efficient
    encoding and decoding. It is designed for scenarios requiring maximum
    performance and minimal overhead.

    Type Parameters:
        MicroPackValue: None, bytes, bool, int, float, str, list, or dict
        MicroPackEncoded: bytes (binary MicroPack format)

    Performance:
        - Encode/decode methods are direct function references for zero overhead
        - No method call indirection or wrapper overhead
    """

    __slots__ = ("encode", "decode", "_codec")

    encode: Callable[[MicroPackSupportedValues], MicroPackEncoded]
    decode: Callable[[MicroPackEncoded], MicroPackSupportedValues]

    def __init__(self) -> None:
        """
        Initialize MicroPack codec with direct function references.

        The encode and decode attributes are set to the underlying codec
        functions directly to avoid any method call overhead.
        """
        self._codec = Codec()
        self.encode: Callable[[MicroPackSupportedValues], MicroPackEncoded] = self._codec.encode
        self.decode: Callable[[MicroPackEncoded], MicroPackSupportedValues] = self._codec.decode
