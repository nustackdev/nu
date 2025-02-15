import abc
from abc import ABC
from typing import Any, Callable, Generic, overload

from .types import DescriptorT, StorageStrategy, ValidationStrategy

__all__ = ["BaseDescriptor"]

class BaseDescriptor(ABC, Generic[DescriptorT], metaclass=abc.ABCMeta):
    def __init__(
        self,
        /,
        *,
        doc: str | None = None,
        validator: Callable[[DescriptorT], bool] | None = None,
        storage: StorageStrategy = ...,
        validation_strategy: ValidationStrategy = ...,
        allow_none: bool = False,
    ) -> None: ...
    def __class_getitem__(cls, type_: type[DescriptorT]) -> type[BaseDescriptor[DescriptorT]]: ...
    def __set_name__(self, owner: type[Any], name: str) -> None: ...
    @overload
    def __get__(self, instance: None, owner: type[Any]) -> BaseDescriptor[DescriptorT]: ...
    @overload
    def __get__(self, instance: Any, owner: type[Any]) -> DescriptorT: ...
    def __set__(self, instance: Any, value: DescriptorT) -> None: ...
    def __delete__(self, instance: Any) -> None: ...
