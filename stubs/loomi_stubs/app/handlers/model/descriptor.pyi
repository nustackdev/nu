from typing import TypeVar, overload

from loomi.app.handlers.state import AsyncStateProtocol, SyncStateProtocol
from loomi.utils.descriptor import BaseDescriptor

from .accesssor_async import AsyncModelValue
from .accesssor_sync import SyncModelValue

__all__ = ["ModelDescriptor", "UseModel"]

StateValueT = TypeVar("StateValueT", bound="StateValue")

class ModelDescriptor(BaseDescriptor[StateValueT]):
    def __init__(
        self, state: type[AsyncStateProtocol | SyncStateProtocol], type: type[StateValueT]
    ) -> None: ...

@overload
def UseModel(
    state: AsyncStateProtocol, type: type[StateValueT]
) -> AsyncModelValue[StateValueT]: ...
@overload
def UseModel(state: SyncStateProtocol, type: type[StateValueT]) -> SyncModelValue[StateValueT]: ...
