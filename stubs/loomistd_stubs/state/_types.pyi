from _typeshed import Incomplete

from loomistd.observer import ObserverCallbackFn

__all__ = ["StateKey", "StateValue", "StateCallbackFn"]

StateKey = tuple[str, ...]
StateValue: Incomplete
StateCallbackFn = ObserverCallbackFn[StateKey]
