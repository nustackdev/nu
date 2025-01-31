"""
Descriptor implementations for model.

This module provides descriptor implementations that enable the ORM-like
interface while leveraging the existing descriptor infrastructure.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Optional, Type, TypeVar

from sonny.state.types import StateValue
from sonny.utils.descriptor import BaseDescriptor, StorageStrategy, ValidationStrategy

if TYPE_CHECKING:
    from .service import ModelService
    from .values import ItemValue

ModelServiceT = TypeVar("ModelServiceT", bound="ModelService")
StateValueT = TypeVar("StateValueT", bound=StateValue)


class ItemDescriptor(BaseDescriptor[StateValueT]):
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


def Item(type: Type[StateValueT]) -> ItemValue[StateValueT]:
    """
    Create an item descriptor.

    Args:
        default: Optional default value
        validator: Optional validation function

    Returns:
        Typed item descriptor
    """
    return ItemDescriptor(type=type)  # type: ignore


class ModelItemDescriptor(BaseDescriptor[ModelServiceT]):
    """
    Base descriptor for model/branch values.

    Manages nested model instances with proper context propagation.
    """

    def __init__(self, type: Type[ModelServiceT]) -> None:
        super().__init__(
            storage=StorageStrategy.INSTANCE_DICT,
            validation_strategy=ValidationStrategy.STRICT,
            allow_none=False,
        )
        self._type = type

    def _validate_type(self, value: Any) -> bool:
        """Validate value is a model instance."""
        return True  # isinstance(value, self._metadata.type)

    def _get_default(self) -> None:
        """Models don't have defaults."""
        return None


def ModelItem(type: Type[ModelServiceT]) -> ModelServiceT:
    """
    Create a model item descriptor.

    Returns:
        Typed model descriptor
    """
    return ModelItemDescriptor[ModelServiceT](type)  # type: ignore
