from typing import Any, Protocol, TypeAlias, runtime_checkable

from .._protocols import CodecProtocol

PassthroughCodecKey: TypeAlias = tuple[str, ...]
PassthroughCodecValue: TypeAlias = Any
PassthroughCodecEncodedKey: TypeAlias = str
PassthroughCodecEncodedValue: TypeAlias = Any


@runtime_checkable
class PassthroughCodecProtocol(
    CodecProtocol[
        PassthroughCodecKey,
        PassthroughCodecValue,
        PassthroughCodecEncodedKey,
        PassthroughCodecEncodedValue,
    ],
    Protocol,
):
    """
    Passthrough codec protocol.
    """

    ...
