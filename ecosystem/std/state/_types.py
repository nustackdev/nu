from typing import TypeAlias

from ecosystem.std.observer import ObserverCallbackFn

StateKey: TypeAlias = tuple[str, ...]
StateValue: TypeAlias = (
    None | bool | int | float | str | list["StateValue"] | dict[str, "StateValue"]
)
StateCallbackFn: TypeAlias = ObserverCallbackFn[StateKey]
