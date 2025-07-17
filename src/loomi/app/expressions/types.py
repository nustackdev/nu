from __future__ import annotations

from typing import TYPE_CHECKING, Literal, TypeAlias

if TYPE_CHECKING:
    pass

__all__ = [
    "ErrorBehavior",
]

ErrorBehavior: TypeAlias = Literal["fail", "continue"]
