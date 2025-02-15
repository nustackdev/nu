from typing import TypeVar, overload

from loomi.app.handlers.state import AsyncStateProtocol, StateValue, SyncStateProtocol
from loomi.utils.descriptor import BaseDescriptor

from .accesssor_async import AsyncModelValue
from .accesssor_sync import SyncModelValue

__all__ = ["StateDescriptor", "UseState"]

StateValueT = TypeVar("StateValueT", bound="StateValue")

class StateDescriptor(BaseDescriptor[StateValueT]):
    def __init__(
        self, state: type[AsyncStateProtocol | SyncStateProtocol], type: type[StateValueT]
    ) -> None: ...

@overload
def UseState(
    state: AsyncStateProtocol, type: type[StateValueT]
) -> AsyncModelValue[StateValueT]: ...
@overload
def UseState(state: SyncStateProtocol, type: type[StateValueT]) -> SyncModelValue[StateValueT]: ...
