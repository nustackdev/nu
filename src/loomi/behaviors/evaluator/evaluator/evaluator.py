from __future__ import annotations

from concurrent.futures import Future
from typing import Any, Callable

import attrs

from loomicore.resource import SyncResource
from loomicore.spec import ResourceSpec, Spec

from ..context import Context
from ..expressions import Expression
from .fleet import AttachFleet, FleetCoordinator


class Evaluator(SyncResource):
    fleet: FleetCoordinator[Any] = AttachFleet()

    def evaluate(
        self,
        expression: Expression,
        context: Context,
    ) -> None:
        """
        Evaluate an expression.
        """
        expression.evaluate(self, context)

    def execute(
        self,
        method: Callable,
        *args: Any,
        **kwargs: Any,
    ) -> Future[Any]:
        """
        Execute a method.
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
        """
        return self.fleet.distribute(method, args_list, kwargs_list)


@attrs.define(frozen=True, slots=True, kw_only=True)
class EvaluatorSpec(ResourceSpec):
    """
    Specification for the Runtime resource.

    This specification defines the configuration for the Runtime resource, including its fleet and other properties.
    """

    name: str = "runtime"
    factory: type = Evaluator
    fleet: tuple[Spec, ...]
