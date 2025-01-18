from typing import Any, Awaitable, Callable

StateKey = tuple[str, ...]
StateValue = Any
StateAsyncCallbackFn = Callable[[StateKey], Awaitable[None]]
StateSyncCallbackFn = Callable[[StateKey], None]
