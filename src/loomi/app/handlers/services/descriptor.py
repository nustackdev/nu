from __future__ import annotations

from typing import Any, Type, TypeVar

from loomi.service import Service, Spec
from loomi.utils.descriptor import BaseDescriptor, StorageStrategy, ValidationStrategy

__all__ = [
    "ServiceDescriptor",
    "UseService",
]


S = TypeVar("S", bound=Service)
T = TypeVar("T")


class ServiceDescriptor(BaseDescriptor[S]):
    """Descriptor for service dependencies with protocol validation."""

    def __init__(
        self,
        default_factory: Type[S] | None = None,
        /,
        *,
        spec: Spec | None = None,
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
        return isinstance(value, (Service,))

    def _get_default(self) -> None:
        """Default value is None until initialized."""
        return None


def UseService(type: type[T], spec: Spec | None = None) -> T:
    """Create a service specification."""
    return ServiceDescriptor[T](spec=spec)  # type: ignore
