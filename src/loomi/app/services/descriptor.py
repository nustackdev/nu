from __future__ import annotations

from typing import Any, Type, TypeVar

from loomi._lib.utils.descriptor import BaseDescriptor, StorageStrategy, ValidationStrategy
from loomi.service import Service, Spec

__all__ = [
    "ServiceDescriptor",
    "UseService",
]


S = TypeVar("S", bound=Service)


class ServiceDescriptor(BaseDescriptor[S]):
    """Descriptor for service dependencies with protocol validation."""

    def __init__(
        self,
        default_factory: Type[S] | None = None,
        /,
        *,
        spec: Spec | None = None,
        spec_key: str | None = None,
        as_state: bool = False,
        as_engine: bool = False,
    ) -> None:
        super().__init__(
            storage=StorageStrategy.WEAKREF,
            validation_strategy=ValidationStrategy.STRICT,
            allow_none=True,
        )
        self.default_factory = default_factory
        self.spec = spec
        self.spec_key = spec_key
        self.as_state = as_state
        self.as_engine = as_engine

    def _validate_type(self, value: Any) -> bool:
        """Validate that value is a subclass of BaseService."""
        return isinstance(value, (Service,))

    def _get_default(self) -> None:
        """Default value is None until initialized."""
        return None


def UseService(type: type[S], spec: Spec | None = None) -> S:
    """Create a service specification."""
    return ServiceDescriptor[S](spec=spec, as_state=False, as_engine=False)  # type: ignore
