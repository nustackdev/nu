from typing import Protocol, TypeVar

__all__ = ["CodecProtocol"]

CodecKeyT = TypeVar("CodecKeyT")
CodecValueT = TypeVar("CodecValueT")
CodecEncodedKeyT = TypeVar("CodecEncodedKeyT")
CodecEncodedValueT = TypeVar("CodecEncodedValueT")

class CodecProtocol(Protocol[CodecKeyT, CodecValueT, CodecEncodedKeyT, CodecEncodedValueT]):
    def encode_key(self, key: CodecKeyT) -> CodecEncodedKeyT: ...
    def decode_key(self, encoded: CodecEncodedKeyT) -> CodecKeyT: ...
    def encode_value(self, value: CodecValueT) -> CodecEncodedValueT: ...
    def decode_value(self, encoded: CodecEncodedValueT) -> CodecValueT: ...
