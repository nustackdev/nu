from __future__ import annotations

from loomi.interfaces.state.types import AsyncCallbackFn, StatePath

__all__ = [
    "StateKey",
    "StateValue",
    "StateCallbackFn",
]

StateKey = StatePath
StateValue = None | bytes | bool | int | float | str | list["StateValue"] | dict[str, "StateValue"]
StateCallbackFn = AsyncCallbackFn
