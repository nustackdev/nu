from __future__ import annotations

from typing import TYPE_CHECKING, Any, Type, TypeVar

from loomi._utils.descriptor import BaseDescriptor, StorageStrategy, ValidationStrategy

if TYPE_CHECKING:
    from loomi._service import Service
    from loomi._spec import Spec

__all__ = [
    "Attach",
    "AttachDescriptor",
    "is_attach_descriptor",
]


S = TypeVar("S", bound="Service")
T = TypeVar("T")


class AttachDescriptor(BaseDescriptor[S]):
    """Descriptor for service dependencies with protocol validation."""

    def __init__(
        self,
        default_factory: Type[S] | None = None,
        /,
        *,
        spec: "Spec | None" = None,
        spec_key: str | None = None,
        allow_override: bool = True,
    ) -> None:
        super().__init__(
            storage=StorageStrategy.WEAKREF,
            validation_strategy=ValidationStrategy.STRICT,
            allow_none=True,
        )
        self.default_factory = default_factory
        self.spec = spec
        self.spec_key = spec_key
        self.allow_override = allow_override

    def _validate_type(self, value: Any) -> bool:
        """Validate that value is a subclass of BaseService."""
        return True

    def _get_default(self) -> None:
        """Default value is None until initialized."""
        return None


def Attach(type: type[T] | None = None, spec: "Spec | None" = None) -> T:
    """Create a service specification."""
    return AttachDescriptor[T](spec=spec)  # type: ignore


def is_attach_descriptor(obj: Any) -> bool:
    """Check if an object is a service specification."""
    return isinstance(obj, AttachDescriptor)
