from __future__ import annotations

import weakref
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Any, Callable, Generic, Type, TypeVar, Union, get_args, get_origin

DescriptorT = TypeVar("DescriptorT")


class StorageStrategy(Enum):
    """Strategy for storing descriptor values."""

    INSTANCE_DICT = auto()  # Store in instance.__dict__
    WEAKREF = auto()  # Store in descriptor's weakref dict


class ValidationStrategy(Enum):
    """Strategy for handling validation failures."""

    STRICT = auto()  # Raise on any validation failure
    COERCE = auto()  # Try to coerce values before validation
    LENIENT = auto()  # Store invalid values but log warning


@dataclass(frozen=True)
class DescriptorMetadata(Generic[DescriptorT]):
    """
    Immutable metadata for descriptors.

    Attributes:
        _name: Internal name of the descriptor
        _type: Type of values the descriptor accepts
        doc: Documentation string
        validator: Optional custom validation function
        storage: Strategy for storing values
        validation_strategy: Strategy for handling validation failures
        allow_none: Whether None values are permitted
    """

    _name: str | None = None
    _type: Type[DescriptorT] | None = None
    doc: str | None = None
    validator: Callable[[DescriptorT], bool] | None = None
    storage: StorageStrategy = StorageStrategy.WEAKREF
    validation_strategy: ValidationStrategy = ValidationStrategy.STRICT
    allow_none: bool = False

    @property
    def type(self) -> Type[DescriptorT]:
        """Get the descriptor's type, raising an error if not set."""
        if self._type is None:
            raise ValueError("Type not set")
        return self._type

    @property
    def name(self) -> str:
        """Get the descriptor's name, raising an error if not set."""
        if self._name is None:
            raise ValueError("Name not set")
        return self._name


@dataclass
class DescriptorState:
    """Mutable state container for descriptors."""

    values: weakref.WeakKeyDictionary = field(default_factory=weakref.WeakKeyDictionary)


def validate_type(value: Any, expected_type: Type[DescriptorT]) -> bool:
    """
    Validate if a value matches an expected type, handling complex types correctly.

    Args:
        value: Value to validate
        expected_type: Type to validate against

    Returns:
        bool: Whether the value matches the type
    """
    if expected_type is Any:
        return True

    origin = get_origin(expected_type)
    if origin is Union:
        return any(validate_type(value, arg) for arg in get_args(expected_type))
    elif origin is not None:
        # Handle generic types
        if not isinstance(value, origin):
            return False
        args = get_args(expected_type)
        if not args:
            return True
        # Validate generic parameters if possible
        if hasattr(value, "__orig_class__"):
            value_args = get_args(value.__orig_class__)
            return all(validate_type(v_arg, t_arg) for v_arg, t_arg in zip(value_args, args))
        return True
    else:
        return isinstance(value, expected_type)
