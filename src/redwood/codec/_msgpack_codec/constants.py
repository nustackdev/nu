from __future__ import annotations

__all__ = [
    "PATH_SEPARATOR",
    "MAX_STR_SIZE",
]

# Reuse constants from binary codec for key encoding
PATH_SEPARATOR: bytes = b"\xfe"
MAX_STR_SIZE: int = 10 * 1024 * 1024  # 10MB
