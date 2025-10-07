from __future__ import annotations


__all__ = [
    "CodecError",
    "EncodeError",
    "DecodeError",
]


class CodecError(Exception):
    """Base exception for codec errors."""

    pass


class EncodeError(CodecError):
    """Raised when encoding fails."""

    pass


class DecodeError(CodecError):
    """Raised when decoding fails."""

    pass
