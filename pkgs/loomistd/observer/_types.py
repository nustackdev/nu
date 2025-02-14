from __future__ import annotations

from typing import Awaitable, Callable, TypeAlias, TypeVar

ObserverKeyT = TypeVar("ObserverKeyT")
ObserverEncodedKeyT = TypeVar("ObserverEncodedKeyT")
ObserverCallbackFn: TypeAlias = Callable[[ObserverKeyT], Awaitable[None]]
