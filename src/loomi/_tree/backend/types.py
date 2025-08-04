from __future__ import annotations

from typing import Any, Callable

__all__ = [
    "KeyBase",
    "Key",
    "Value",
    "CallbackFn",
]

KeyBase = str
Key = tuple[KeyBase, ...]
Value = Any
CallbackFn = Callable[[Key], None]
