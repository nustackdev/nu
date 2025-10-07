from typing import Any


PassthroughCodecValue = Any
PassthroughCodecEncodedValue = Any


MsgpackCodecValue = (
    None
    | bytes
    | bool
    | int
    | float
    | str
    | list["MsgpackCodecValue"]
    | dict[str, "MsgpackCodecValue"]
)
MsgpackCodecEncodedValue = bytes


JSONCodecValue = (
    None | bytes | bool | int | float | str | list["JSONCodecValue"] | dict[str, "JSONCodecValue"]
)
JSONCodecEncodedValue = str
