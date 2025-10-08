"""Pickle codec adapter - Python object serialization."""

from __future__ import annotations

import pickle  # nosec: B403
from collections.abc import Callable

from ..protocols import ValueCodecProtocol
from .types import PickleEncoded, PickleSupportedValues


__all__ = ["PickleCodec"]


class PickleCodec(ValueCodecProtocol[PickleSupportedValues, PickleEncoded]):
    """
    Codec using Python's pickle for arbitrary object serialization.

    Pickle can serialize most Python objects, making it suitable for cases
    where complex object graphs need to be persisted. However, pickle is
    Python-specific and has security implications for untrusted data.

    Type Parameters:
        PickleValue: Any picklable Python object
        PickleEncoded: bytes (Python pickle format)

    Performance:
        - Encode/decode methods are direct function references for zero overhead
        - No method call indirection or wrapper overhead

    Security:
        WARNING: Only use with trusted data. Pickle can execute arbitrary code
        during deserialization.
    """

    encode: Callable[[PickleSupportedValues], PickleEncoded]
    decode: Callable[[PickleEncoded], PickleSupportedValues]

    def __init__(self) -> None:
        """
        Initialize pickle codec with direct function references.

        The encode and decode attributes are set to pickle module functions
        directly to avoid any method call overhead.
        """
        self.encode = pickle.dumps
        self.decode = pickle.loads
