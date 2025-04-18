from __future__ import annotations

from typing import TYPE_CHECKING, Literal

if TYPE_CHECKING:
    pass

__all__ = [
    "ErrorBehavior",
]

ErrorBehavior = Literal["fail", "continue"]
