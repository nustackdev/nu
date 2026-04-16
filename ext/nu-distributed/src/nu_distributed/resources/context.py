"""ContextResource - composables Resource that builds an everybase Context.

Attaches a NavigatorResource and binds it as Navigator to the Context.
"""

from __future__ import annotations

import attrs
from composables import Attach, Resource, ResourceSpec

from nu import Context

from .navigator import NavigatorSpec


__all__ = [
    "ContextResource",
    "ContextSpec",
]


class ContextResource(Resource):
    """Builds an everybase Context with attached Navigator bound."""

    spec: ContextSpec
    storage = Attach()

    async def setup(self) -> None:
        """Build Context and bind the Navigator."""
        from virtuals import Navigator

        self._ctx = Context()
        self._ctx = self._ctx.bind(Navigator, self.storage)

    @property
    def ctx(self) -> Context:
        """The everybase Context, ready for flow execution."""
        return self._ctx


@attrs.define(frozen=True, slots=True, kw_only=True)
class ContextSpec(ResourceSpec):
    """Spec for ContextResource."""

    factory: type = ContextResource
    name: str = "context"

    storage: NavigatorSpec = attrs.Factory(NavigatorSpec)
