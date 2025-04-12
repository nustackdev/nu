from typing import Awaitable, Callable

StatePathComponent = str
StatePath = tuple[StatePathComponent, ...]
StateValue = None | bytes | bool | int | float | str | list["StateValue"] | dict[str, "StateValue"]

AsyncStateCallbackFn = Callable[[StatePath], Awaitable[None]]
SyncStateCallbackFn = Callable[[StatePath], None]
