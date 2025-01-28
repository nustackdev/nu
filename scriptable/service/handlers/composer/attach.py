from __future__ import annotations

from typing import TYPE_CHECKING, Any, Type, TypeVar

from scriptable.utils.descriptor import BaseDescriptor, StorageStrategy, ValidationStrategy

if TYPE_CHECKING:
    from scriptable.service.base import ServiceType, Spec


S = TypeVar("S", bound="ServiceType")
T = TypeVar("T")


class AttachDescriptor(BaseDescriptor[S]):
    """Descriptor for memory dependencies with protocol validation."""

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
        return isinstance(value, "ServiceType")

    def _get_default(self) -> None:
        """Default value is None until initialized."""
        return None


def Attach(type: type[T], spec: "Spec | None" = None) -> T:
    """Create a memory specification."""
    return AttachDescriptor[T](spec=spec)  # type: ignore


def is_attach_descriptor(obj: Any) -> bool:
    """Check if an object is a memory specification."""
    return isinstance(obj, AttachDescriptor)
