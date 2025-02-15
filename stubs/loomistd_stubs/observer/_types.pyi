from typing import Awaitable, Callable, TypeVar

__all__ = ["ObserverKeyT", "ObserverEncodedKeyT", "ObserverCallbackFn"]

ObserverKeyT = TypeVar("ObserverKeyT")
ObserverEncodedKeyT = TypeVar("ObserverEncodedKeyT")
ObserverCallbackFn = Callable[[ObserverKeyT], Awaitable[None]]
