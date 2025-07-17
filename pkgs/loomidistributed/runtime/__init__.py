from __future__ import annotations

from concurrent.futures import Future
from typing import Any, Callable

import attrs

from loomicore.attach import Attach
from loomicore.resource import SyncResource
from loomicore.spec import ResourceSpec, Spec
from loomidistributed.coordinators.fleet import AttachFleet, FleetCoordinator


class Runtime(SyncResource):
    fleet: FleetCoordinator[Any] = AttachFleet()

    def execute(
        self,
        method: Callable,
        *args: Any,
        **kwargs: Any,
    ) -> Future[Any]:
        """
        Execute the runtime logic synchronously.

        This method should be overridden by subclasses to implement specific execution logic.
        """
        return self.fleet.submit(method, *args, **kwargs)

    def execute_distributed(
        self,
        method: Callable,
        args_list: list[tuple[Any, ...]],
        kwargs_list: list[dict[str, Any]] | None = None,
    ) -> list[Future[Any]]:
        """
        Execute the runtime logic in a distributed manner.

        This method should be overridden by subclasses to implement specific distributed execution logic.
        """
        return self.fleet.distribute(method, args_list, kwargs_list)


@attrs.define(frozen=True, slots=True, kw_only=True)
class RuntimeSpec(ResourceSpec):
    """
    Specification for the Runtime resource.

    This specification defines the configuration for the Runtime resource, including its fleet and other properties.
    """

    name: str = "runtime"
    factory: type[Runtime] = Runtime
    fleet: tuple[Spec, ...]
