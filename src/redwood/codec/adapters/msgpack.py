from __future__ import annotations


try:
    import msgpack
except ImportError as e:
    raise ImportError(
        "msgpack is required for MsgPackCodec. Please install it via 'pip install msgpack'"
    ) from e


__all__ = [
    "MsgPackCodec",
]


class MsgPackCodec:
    def __init__(self) -> None:
        self.encode = msgpack.packb
        self.decode = msgpack.unpackb
