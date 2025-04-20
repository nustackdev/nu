from __future__ import annotations

from typing import TYPE_CHECKING, Any, Type, TypeVar, cast

from loomi._utils.descriptor import BaseDescriptor, StorageStrategy, ValidationStrategy

if TYPE_CHECKING:
    from loomi._service import Service
    from loomi._spec import Spec

__all__ = [
    "ServiceDescriptor",
    "UseService",
]


S = TypeVar("S", bound="Service")


class ServiceDescriptor(BaseDescriptor[S]):
    """Descriptor for service dependencies with protocol validation."""

    def __init__(
        self,
        default_factory: Type[S] | None = None,
        /,
        *,
        spec: "Spec | None" = None,
        spec_key: str | None = None,
    ) -> None:
        super().__init__(
            storage=StorageStrategy.WEAKREF,
            validation_strategy=ValidationStrategy.STRICT,
            allow_none=True,
        )
        self.default_factory = default_factory
        self.spec = spec
        self.spec_key = spec_key

    def _validate_type(self, value: Any) -> bool:
        """Validate that value is a subclass of BaseService."""
        return True

    def _get_default(self) -> None:
        """Default value is None until initialized."""
        return None


def UseService(spec: "Spec | None" = None) -> S:  # type: ignore
    """Create a service specification."""
    return cast(S, ServiceDescriptor[S](spec=spec))
