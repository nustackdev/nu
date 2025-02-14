from typing import Protocol, TypeAlias, runtime_checkable

from .._protocols import CodecProtocol

JSONCodecKey: TypeAlias = tuple[str, ...]
JSONCodecValue: TypeAlias = (
    None | bool | int | float | str | list["JSONCodecValue"] | dict[str, "JSONCodecValue"]
)
JSONCodecEncodedKey: TypeAlias = str
JSONCodecEncodedValue: TypeAlias = str


@runtime_checkable
class JSONCodecProtocol(
    CodecProtocol[JSONCodecKey, JSONCodecValue, JSONCodecEncodedKey, JSONCodecEncodedValue],
    Protocol,
):
    """
    JSON codec protocol.
    """

    ...
