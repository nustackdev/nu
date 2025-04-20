from __future__ import annotations

from typing import TYPE_CHECKING, Any, TypeVar, cast

from loomi._utils.descriptor import BaseDescriptor, StorageStrategy, ValidationStrategy

if TYPE_CHECKING:
    from loomi._app import AsyncApp, SyncApp
    from loomi._spec import Spec

__all__ = [
    "AppDescriptor",
    "UseApp",
]

S = TypeVar("S", bound="AsyncApp | SyncApp")


class AppDescriptor(BaseDescriptor[S]):
    """Descriptor for service dependencies with protocol validation."""

    def __init__(
        self,
        app: type[S],
        /,
        *,
        spec: "Spec | None" = None,
    ) -> None:
        super().__init__(
            storage=StorageStrategy.WEAKREF,
            validation_strategy=ValidationStrategy.STRICT,
            allow_none=True,
        )
        self.app = app
        self.spec = spec

    def _validate_type(self, value: Any) -> bool:
        """Validate that value is a subclass of BaseService."""
        return True

    def _get_default(self) -> None:
        """Default value is None until initialized."""
        return None


def UseApp(app: type[S], spec: "Spec | None" = None) -> S:
    """Create a service specification."""
    return cast(S, AppDescriptor[S](app, spec=spec))
