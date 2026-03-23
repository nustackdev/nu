"""NavigatorResource - composables Resource wrapping a virtuals Navigator.

Navigator is the high-level entrypoint for storage access.
Attaches a storage resource and optional observer resource.
"""

from __future__ import annotations

import attrs
from composables import Attach, Resource, ResourceSpec
from virtuals import Navigator
from virtuals.views import DictView

from .storage import InMemoryStorageSpec


__all__ = [
    "NavigatorResource",
    "NavigatorSpec",
]


class NavigatorResource(Resource, Navigator):
    """Resource that IS a Navigator. transaction(), snapshot() work directly."""

    spec: NavigatorSpec
    storage_resource = Attach()

    def __init__(self, spec: object = None, /) -> None:
        Resource.__init__(self, spec)

    async def setup(self) -> None:
        """Init Navigator with attached storage (already opened by composables)."""
        Navigator.__init__(self, self.storage_resource, self.spec.root_view)
        self._opened = True


@attrs.define(frozen=True, slots=True, kw_only=True)
class NavigatorSpec(ResourceSpec):
    """Spec for NavigatorResource."""

    factory: type = NavigatorResource
    name: str = "navigator"

    storage_resource: InMemoryStorageSpec = attrs.Factory(InMemoryStorageSpec)
    root_view: type = DictView
