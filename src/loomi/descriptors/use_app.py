from __future__ import annotations

from typing import TYPE_CHECKING, Any, TypeVar

from loomi.utils.descriptor import BaseDescriptor, StorageStrategy, ValidationStrategy

if TYPE_CHECKING:
    from loomi.app import App
    from loomi.spec import Spec

__all__ = [
    "AppDescriptor",
    "UseApp",
]

S = TypeVar("S", bound="App")


class AppDescriptor(BaseDescriptor[S]):
    """Descriptor for service dependencies with protocol validation."""

    def __init__(
        self,
        app: type[S],
        /,
        *,
        service_specs: "dict[str, Spec] | None" = None,
    ) -> None:
        super().__init__(
            storage=StorageStrategy.WEAKREF,
            validation_strategy=ValidationStrategy.STRICT,
            allow_none=True,
        )
        self.app = app
        self.service_specs = service_specs

    def _validate_type(self, value: Any) -> bool:
        """Validate that value is a subclass of BaseService."""
        return True

    def _get_default(self) -> None:
        """Default value is None until initialized."""
        return None


def UseApp(app: type[S], service_specs: "dict[str, Spec] | None" = None) -> S:
    """Create a service specification."""
    return AppDescriptor[S](  # type: ignore
        app,
        service_specs=service_specs,
    )
