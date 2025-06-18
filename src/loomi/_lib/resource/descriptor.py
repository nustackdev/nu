from __future__ import annotations

from typing import TYPE_CHECKING, Any, TypeVar

from loomi._utils.descriptor import BaseDescriptor, StorageStrategy, ValidationStrategy

if TYPE_CHECKING:
    from .resource import Resource
    from .spec import Spec

__all__ = [
    "ResourceDescriptor",
]


S = TypeVar("S", bound="Resource")


class ResourceDescriptor(BaseDescriptor[S]):
    """Descriptor for service dependencies with protocol validation."""

    def __init__(
        self,
        spec: "Spec | None" = None,
        /,
        *,
        alias: str | None = None,
    ) -> None:
        super().__init__(
            storage=StorageStrategy.WEAKREF,
            validation_strategy=ValidationStrategy.STRICT,
            allow_none=True,
        )
        self.spec = spec
        self.alias = alias

    def _validate_type(self, value: Any) -> bool:
        """Validate that value is a subclass of BaseResource."""
        return True

    def _get_default(self) -> None:
        """Default value is None until initialized."""
        return None
