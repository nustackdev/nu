from __future__ import annotations

from loomistd.observer import ObserverCallbackFn

__all__ = [
    "StateKey",
    "StateValue",
    "StateCallbackFn",
]

StateKey = tuple[str, ...]
StateValue = None | bool | int | float | str | list["StateValue"] | dict[str, "StateValue"]
StateCallbackFn = ObserverCallbackFn[StateKey]
