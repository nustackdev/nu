from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import asdict
from typing import Any, Callable, Generic, Type, TypeGuard, overload

from .exceptions import TypeValidationError, ValueValidationError
from .logger import logger
from .types import (
    DescriptorMetadata,
    DescriptorState,
    DescriptorT,
    StorageStrategy,
    ValidationStrategy,
)


class BaseDescriptor(Generic[DescriptorT], ABC):
    """
    Abstract base class for descriptors with type safety and validation.

    Type Parameters:
        T: The type of value this descriptor will hold

    Attributes:
        _metadata: Immutable descriptor spec
        _state: Mutable descriptor state
    """

    __slots__ = ("_metadata", "_state")

    def __init__(
        self,
        /,
        *,
        doc: str | None = None,
        validator: Callable[[DescriptorT], bool] | None = None,
        storage: StorageStrategy = StorageStrategy.WEAKREF,
        validation_strategy: ValidationStrategy = ValidationStrategy.STRICT,
        allow_none: bool = False,
    ) -> None:
        """
        Initialize the descriptor.

        Args:
            doc: Documentation string
            validator: Optional function to validate values
            storage: Strategy for storing values
            validation_strategy: Strategy for handling validation failures
            allow_none: Whether None values are permitted
        """
        self._metadata: DescriptorMetadata[DescriptorT] = DescriptorMetadata[DescriptorT](
            doc=doc or self.__class__.__doc__,
            validator=validator,
            storage=storage,
            validation_strategy=validation_strategy,
            allow_none=allow_none,
        )
        self._state = DescriptorState()

    def __class_getitem__(cls, type_: Type[DescriptorT]) -> Type[BaseDescriptor[DescriptorT]]:
        """Creates a new descriptor class with bound type."""

        class TypeBoundDescriptor(cls):
            def __init__(self, *args, **kwargs):
                super().__init__(*args, **kwargs)
                md = asdict(self._metadata)
                md.update({"_type": type_})
                self._metadata = DescriptorMetadata[type_](**md)

        return TypeBoundDescriptor

    def __set_name__(self, owner: Type[Any], name: str) -> None:
        """Set descriptor name when class is created."""
        md = asdict(self._metadata)
        md.update({"_name": name})
        self._metadata = DescriptorMetadata[DescriptorT](**md)

    @overload
    def __get__(self, instance: None, owner: Type[Any]) -> BaseDescriptor[DescriptorT]: ...

    @overload
    def __get__(self, instance: Any, owner: Type[Any]) -> DescriptorT: ...

    def __get__(
        self, instance: Any | None, owner: Type[Any]
    ) -> DescriptorT | BaseDescriptor[DescriptorT]:
        """Get value with proper type handling."""
        if instance is None:
            return self

        if self._metadata.storage == StorageStrategy.INSTANCE_DICT:
            try:
                return instance.__dict__[self._metadata.name]
            except KeyError:
                raise AttributeError(
                    f"'{instance.__class__.__name__}' object has no attribute '{self._metadata.name}'"
                )

        return self._state.values.get(instance, self._get_default())

    def __set__(self, instance: Any, value: DescriptorT) -> None:
        """Set value with validation."""
        if value is None:
            if not self._metadata.allow_none:
                raise TypeValidationError(
                    "None value not allowed",
                    self._metadata.name,
                    value,
                    self._metadata.type,
                )
        else:
            try:
                if not self._validate_type(value):
                    raise TypeValidationError(
                        "Type validation failed",
                        self._metadata.name,
                        value,
                        self._metadata.type,
                    )

                if self._metadata.validator:
                    if not self._metadata.validator(value):
                        msg = f"Custom validation failed for {self._metadata.name}"
                        if self._metadata.validation_strategy == ValidationStrategy.STRICT:
                            raise ValueValidationError(
                                msg, self._metadata.name, value, self._metadata.type
                            )
                        logger.warning(
                            msg,
                            extra={
                                "field": self._metadata.name,
                                "value": value,
                                "type": self._metadata.type,
                            },
                        )
            except Exception as e:
                if self._metadata.validation_strategy == ValidationStrategy.STRICT:
                    raise
                logger.error(f"Validation error: {str(e)}", exc_info=True)

        if self._metadata.storage == StorageStrategy.INSTANCE_DICT:
            instance.__dict__[self._metadata.name] = value
        else:
            self._state.values[instance] = value

    def __delete__(self, instance: Any) -> None:
        """Delete value with proper cleanup."""
        if self._metadata.storage == StorageStrategy.INSTANCE_DICT:
            instance.__dict__.pop(self._metadata.name, None)
        else:
            self._state.values.pop(instance, None)

    def _validate_type(self, value: Any) -> TypeGuard[DescriptorT]:
        """
        Custom type validation logic.

        Args:
            value: Value to validate

        Returns:
            T: Validated value

        Raises:
            TypeValidationError: If type validation fails
        """
        return isinstance(value, self._metadata.type)

    @abstractmethod
    def _get_default(self) -> DescriptorT:
        """
        Get default value for the type.

        Returns:
            T: Default value
        """
        raise NotImplementedError
