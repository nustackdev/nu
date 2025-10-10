"""Pickle codec adapter - Python object serialization."""

from __future__ import annotations

import pickle  # nosec: S403
from typing import TYPE_CHECKING

from ..protocols import ValueCodecProtocol
from .types import PickleEncoded, PickleSupportedValues


__all__ = ["PickleCodec"]


class PickleCodec:
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

    def __init__(self) -> None:
        """
        Initialize pickle codec with direct function references.

        The encode and decode attributes are set to pickle module functions
        directly to avoid any method call overhead.
        """
        self.encode = pickle.dumps  # type: ignore[return-value]
        self.decode = pickle.loads  # type: ignore[return-value]

    def encode(self, value: PickleSupportedValues) -> PickleEncoded:
        """Encode a supported value into pickle binary format."""
        ...

    def decode(self, encoded: PickleEncoded) -> PickleSupportedValues:
        """Decode pickle binary data back into a supported value."""
        ...


if TYPE_CHECKING:
    _: type[ValueCodecProtocol[PickleSupportedValues, PickleEncoded]] = PickleCodec
