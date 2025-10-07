from __future__ import annotations


try:
    from micropack import Codec
except ImportError as e:
    raise ImportError(
        "micropack is required for MicroPackCodec. Please install it via 'pip install micropack'"
    ) from e


__all__ = [
    "MicroPackCodec",
]


class MicroPackCodec:
    def __init__(self):
        self._codec = Codec()
        self.encode = self._codec.encode
        self.decode = self._codec.decode
