"""Storage common types."""

from __future__ import annotations

from collections.abc import Callable

from everyshape.loc import key


__all__ = [
    "CallbackFn",
]

type CallbackFn = Callable[[key.Key], None]
