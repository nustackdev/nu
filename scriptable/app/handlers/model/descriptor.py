"""
Descriptor implementations for model.

This module provides descriptor implementations that enable the ORM-like
interface while leveraging the existing descriptor infrastructure.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Optional, Type, TypeVar

from scriptable.app.handlers.state.types import StateValue
from scriptable.utils.descriptor import BaseDescriptor, StorageStrategy, ValidationStrategy

if TYPE_CHECKING:
    from .accesssor import ModelValue

StateValueT = TypeVar("StateValueT", bound=StateValue)


class StateDescriptor(BaseDescriptor[StateValueT]):
    """
    Base descriptor for leaf values.

    Leverages BaseDescriptor for core functionality while adding
    state-specific behavior.
    """

    def __init__(
        self,
        type: Type[StateValueT],
    ) -> None:
        super().__init__(
            storage=StorageStrategy.INSTANCE_DICT,
            validation_strategy=ValidationStrategy.STRICT,
            allow_none=True,
        )
        self._type = type

    def _validate_type(self, value: Any) -> bool:
        """Validate value matches descriptor type."""
        return True  # isinstance(value, self._metadata.type)

    def _get_default(self) -> Optional[StateValueT]:
        """Get default value if any."""
        return None


def UseState(type: Type[StateValueT]) -> ModelValue[StateValueT]:
    """
    Create an item descriptor.

    Args:
        default: Optional default value
        validator: Optional validation function

    Returns:
        Typed item descriptor
    """
    return StateDescriptor(type=type)  # type: ignore
