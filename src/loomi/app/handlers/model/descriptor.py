"""
Descriptor implementations for model.

This module provides descriptor implementations that enable the ORM-like
interface while leveraging the existing descriptor infrastructure.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Type, TypeVar, overload

from loomi.utils.descriptor import BaseDescriptor, StorageStrategy, ValidationStrategy

if TYPE_CHECKING:
    from loomi.app.handlers.state import AsyncStateProtocol, StateValue, SyncStateProtocol

    from .accesssor_async import AsyncModelValue
    from .accesssor_sync import SyncModelValue

__all__ = [
    "StateDescriptor",
    "UseState",
]

StateValueT = TypeVar("StateValueT", bound="StateValue")


class StateDescriptor(BaseDescriptor[StateValueT]):
    """
    Base descriptor for leaf values.

    Leverages BaseDescriptor for core functionality while adding
    state-specific behavior.
    """

    def __init__(
        self,
        state: "Type[AsyncStateProtocol | SyncStateProtocol]",
        type: Type[StateValueT],
    ) -> None:
        super().__init__(
            storage=StorageStrategy.INSTANCE_DICT,
            validation_strategy=ValidationStrategy.STRICT,
            allow_none=True,
        )
        self._state = state
        self._type = type

    def _validate_type(self, value: Any) -> bool:
        """Validate value matches descriptor type."""
        return True  # isinstance(value, self._metadata.type)

    def _get_default(self) -> StateValueT | None:
        """Get default value if any."""
        return None


@overload
def UseState(
    state: "AsyncStateProtocol",
    type: Type[StateValueT],
) -> "AsyncModelValue[StateValueT]": ...


@overload
def UseState(
    state: "SyncStateProtocol",
    type: Type[StateValueT],
) -> "SyncModelValue[StateValueT]": ...


def UseState(
    state: "AsyncStateProtocol | SyncStateProtocol",
    type: Type[StateValueT],
) -> "AsyncModelValue[StateValueT] | SyncModelValue[StateValueT]":
    """
    Create an item descriptor.

    Args:
        default: Optional default value
        validator: Optional validation function

    Returns:
        Typed item descriptor
    """
    return StateDescriptor(state=state, type=type)  # type: ignore
