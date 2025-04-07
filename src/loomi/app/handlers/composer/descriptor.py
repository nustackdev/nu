from __future__ import annotations

from typing import Any, TypeVar

from loomi.app.base import App, AsyncApp, SyncApp
from loomi.service import Spec
from loomi.utils.descriptor import BaseDescriptor, StorageStrategy, ValidationStrategy

__all__ = [
    "AppDescriptor",
    "UseApp",
]


S = TypeVar("S", bound=AsyncApp | SyncApp)


class AppDescriptor(BaseDescriptor[S]):
    """Descriptor for service dependencies with protocol validation."""

    def __init__(
        self,
        app: type[S],
        /,
        *,
        service_specs: dict[str, Spec] | None = None,
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
        return isinstance(value, (App,))

    def _get_default(self) -> None:
        """Default value is None until initialized."""
        return None


def UseApp(app: type[S], service_specs: dict[str, Spec] | None = None) -> S:
    """Create a service specification."""
    return AppDescriptor[S](  # type: ignore
        app,
        service_specs=service_specs,
    )
