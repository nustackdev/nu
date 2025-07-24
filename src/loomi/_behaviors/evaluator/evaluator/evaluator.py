"""
Evaluator - Core Expression Evaluation Engine

This module implements the main Evaluator resource that coordinates expression
execution using a fleet of workers. It provides both single and distributed
execution capabilities.
"""

from __future__ import annotations

from concurrent.futures import Future
from typing import TYPE_CHECKING, Any, Callable

import attrs

from loomicore.attach import Attach
from loomicore.resource import SyncResource
from loomicore.spec import ResourceSpec, Spec

from ..context import Context
from ..exceptions import EvaluationError, FleetError
from ..expressions import Expression
from .fleet import AttachFleet, FleetCoordinator
from .logger import logger

if TYPE_CHECKING:
    from loomi.state import State, Tree


class Evaluator(SyncResource):
    """
    Core expression evaluation engine.

    The Evaluator coordinates expression execution using a fleet of workers,
    providing both single and distributed execution capabilities.

    Attributes:
        fleet: Fleet coordinator for distributed execution
    """

    fleet: FleetCoordinator[Any] = AttachFleet()
    state_service: "State" = Attach()

    @property
    def state(self) -> "Tree":
        return self.state_service.tree

    def evaluate(
        self,
        expression: Expression,
        context: Context,
    ) -> None:
        """
        Evaluate an expression within the given context.

        Args:
            expression: The expression to evaluate
            context: The execution context containing state and metadata

        Raises:
            EvaluationError: If evaluation fails and error_behavior is "fail"
        """
        expression_name = expression.__class__.__name__
        expression_id = id(expression)

        logger.info(
            "Starting evaluation of expression",
            extra={
                "expression_type": expression_name,
                "expression_id": expression_id,
                "context_attributes": list(context.attributes.keys()),
            },
        )

        try:
            # Delegate to the expression's evaluate method
            expression.evaluate(self, context)

            logger.debug(
                "Successfully completed expression evaluation",
                extra={
                    "expression_type": expression_name,
                    "expression_id": expression_id,
                },
            )

        except Exception as e:
            logger.error(
                "Expression evaluation failed",
                extra={
                    "expression_type": expression_name,
                    "expression_id": expression_id,
                    "error_type": type(e).__name__,
                    "error_message": str(e),
                },
                exc_info=True,
            )

            # Wrap the exception in an EvaluationError for better context
            evaluation_error = EvaluationError(
                f"Failed to evaluate {expression_name}: {e}", expression=expression, cause=e
            )

            # Handle error according to expression's error behavior
            if hasattr(expression, "_error_behavior") and expression.error_behavior == "continue":
                logger.warning(
                    "Continuing execution despite evaluation error",
                    extra={
                        "expression_type": expression_name,
                        "expression_id": expression_id,
                    },
                )

                # Execute on_fail expression if configured
                if hasattr(expression, "_on_fail") and expression.on_fail is not None:
                    try:
                        logger.info(
                            "Executing on_fail expression",
                            extra={
                                "expression_type": expression_name,
                                "expression_id": expression_id,
                                "on_fail_type": expression.on_fail.__class__.__name__,
                            },
                        )
                        expression.on_fail.evaluate(self, context)
                    except Exception as on_fail_error:
                        logger.error(
                            "on_fail expression execution failed",
                            extra={
                                "expression_type": expression_name,
                                "expression_id": expression_id,
                                "on_fail_error": str(on_fail_error),
                            },
                            exc_info=True,
                        )
            else:
                # Re-raise as EvaluationError
                raise evaluation_error from e

    def execute(
        self,
        method: Callable,
        *args: Any,
        **kwargs: Any,
    ) -> Future[Any]:
        """
        Execute a method using the fleet coordinator.

        Submits a method for execution on the next available worker in the fleet
        using round-robin distribution.

        Args:
            method: The callable method to execute
            *args: Positional arguments to pass to the method
            **kwargs: Keyword arguments to pass to the method

        Returns:
            Future object representing the pending execution

        Raises:
            FleetError: If fleet coordination fails
        """
        method_name = getattr(method, "__name__", str(method))

        logger.debug(
            "Submitting method for execution",
            extra={
                "method_name": method_name,
                "args_count": len(args),
                "kwargs_keys": list(kwargs.keys()),
                "fleet_size": (
                    len(self.fleet._resources) if hasattr(self.fleet, "_resources") else 0
                ),
            },
        )

        try:
            future = self.fleet.submit(method, *args, **kwargs)

            logger.debug(
                "Method successfully submitted to fleet",
                extra={
                    "method_name": method_name,
                    "future_id": id(future),
                },
            )

            return future

        except Exception as e:
            logger.error(
                "Failed to submit method to fleet",
                extra={
                    "method_name": method_name,
                    "error_type": type(e).__name__,
                    "error_message": str(e),
                },
                exc_info=True,
            )

            raise FleetError(f"Failed to execute method {method_name}: {e}", cause=e) from e

    def execute_distributed(
        self,
        method: Callable,
        args_list: list[tuple[Any, ...]],
        kwargs_list: list[dict[str, Any]] | None = None,
    ) -> list[Future[Any]]:
        """
        Execute a method in a distributed manner across the fleet.

        Distributes multiple method calls across available workers in the fleet,
        enabling parallel execution of the same method with different arguments.

        Args:
            method: The callable method to execute
            args_list: List of argument tuples, one per execution
            kwargs_list: Optional list of keyword argument dicts, one per execution

        Returns:
            List of Future objects representing the pending executions

        Raises:
            FleetError: If fleet coordination fails
            ValueError: If args_list and kwargs_list have mismatched lengths
        """
        method_name = getattr(method, "__name__", str(method))
        job_count = len(args_list)

        # Validate input arguments
        if kwargs_list is not None and len(kwargs_list) != job_count:
            error_msg = f"args_list length ({job_count}) != kwargs_list length ({len(kwargs_list)})"
            logger.error(
                "Mismatched argument list lengths for distributed execution",
                extra={
                    "method_name": method_name,
                    "args_list_length": job_count,
                    "kwargs_list_length": len(kwargs_list),
                },
            )
            raise ValueError(error_msg)

        logger.info(
            "Starting distributed execution",
            extra={
                "method_name": method_name,
                "job_count": job_count,
                "fleet_size": (
                    len(self.fleet._resources) if hasattr(self.fleet, "_resources") else 0
                ),
                "has_kwargs": kwargs_list is not None,
            },
        )

        try:
            futures = self.fleet.distribute(method, args_list, kwargs_list)

            logger.info(
                "Distributed execution successfully submitted",
                extra={
                    "method_name": method_name,
                    "job_count": job_count,
                    "futures_count": len(futures),
                },
            )

            return futures

        except Exception as e:
            logger.error(
                "Failed to execute distributed method",
                extra={
                    "method_name": method_name,
                    "job_count": job_count,
                    "error_type": type(e).__name__,
                    "error_message": str(e),
                },
                exc_info=True,
            )

            raise FleetError(
                f"Failed to execute distributed method {method_name}: {e}", cause=e
            ) from e


@attrs.define(frozen=True, slots=True, kw_only=True)
class EvaluatorSpec(ResourceSpec):
    """
    Specification for the Runtime resource.

    This specification defines the configuration for the Runtime resource, including its fleet and other properties.
    """

    name: str = "runtime"
    factory: type = Evaluator
    fleet: tuple[Spec, ...]
    state_service: Spec
