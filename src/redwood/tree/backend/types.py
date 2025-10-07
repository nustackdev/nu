from __future__ import annotations

from collections.abc import Callable
from typing import Any


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
