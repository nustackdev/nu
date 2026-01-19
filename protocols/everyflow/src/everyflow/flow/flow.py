"""Base Flow class - core execution infrastructure."""

from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, TypeVar

import attrs

from everyflow.runtime import Path, Runtime, RuntimeProtocol, Services, StorageProvider
from everyterm.term import RValue, Term

from ..exceptions import CancelledError


if TYPE_CHECKING:
    from everyterm.typing import Sentinel


__all__ = ["Flow", "is_flow"]

T = TypeVar("T")

logger = logging.getLogger(__name__)


@attrs.define
class Flow[RuntimeT: RuntimeProtocol](ABC):
    """Base class for all flows - handles core execution infrastructure.

    Flows orchestrate execution. They can contain:
    - Other Flows (composition)
    - EveryShape Terms (data operations)

    Subclasses implement `run()` for business logic.
    Base `execute()` handles infrastructure (cancellation, errors).
    """

    # =========================================================================
    # Execution
    # =========================================================================

    async def start_flow(
        self, storage: StorageProvider, runtime_cls: type[RuntimeT] = Runtime
    ) -> None:
        """Start flow execution from root.

        Args:
            storage: Storage provider instance
            runtime_cls: Runtime class to instantiate
        """
        services = Services.create(storage)
        path = Path.root().child(0)
        runtime = runtime_cls(path=path, storage=storage, services=services)

        runtime.state.init_flow_state()

        await self.execute(runtime)

    async def execute(self, runtime: RuntimeT) -> None:
        """Execute flow with infrastructure handling.

        Never override. Implement run() instead.
        """
        runtime.state.init_flow_step_state(runtime.path)

        if runtime.cancellation.is_cancelled(runtime.path):
            return

        runtime.checkpoint.set_started(runtime.path)

        try:
            await self.run(runtime)
        except CancelledError:
            logger.debug("Flow is cancelled")
            # TODO: set cancelled status
        except Exception as e:
            logger.exception(f"Error with Flow {self}")
            runtime.checkpoint.set_error(runtime.path, str(e))
            raise e
        else:
            runtime.checkpoint.set_finished(runtime.path)

    @abstractmethod
    async def run(self, runtime: RuntimeT) -> None:
        """Execute flow business logic.

        To be implemented by subclasses.
        """
        ...

    # =========================================================================
    # Child Execution
    # =========================================================================

    async def execute_child(
        self, child: Flow | Term, child_index: str | int, runtime: RuntimeT
    ) -> None:
        """Execute child (Flow or Term) within current flow's runtime.

        Args:
            child: Child to execute
            child_index: Index of child in parent's children
            runtime: Current runtime
        """
        if isinstance(child, Flow):
            await self.execute_child_flow(child, child_index, runtime)
        elif isinstance(child, Term):
            await self.execute_child_term(child, child_index, runtime)
        else:
            raise ValueError(f"Unsupported flow step structure: {child.__class__.__name__}")

    async def execute_child_flow(
        self, child: Flow, child_index: str | int, runtime: RuntimeT
    ) -> None:
        """Execute child Flow within current flow's runtime.

        Args:
            child: Child Flow to execute
            child_index: Index of child in parent's children
            runtime: Current runtime
        """
        child_runtime = runtime.child(child_index)
        await child.execute(child_runtime)

    async def execute_child_term(
        self, child: Term, child_index: str | int, runtime: RuntimeT
    ) -> None:
        """Execute child Term within current flow's runtime.

        Args:
            child: Child Term to execute
            child_index: Index of child in parent's children
            runtime: Current runtime
        """
        child_runtime = runtime.child(child_index)

        child_runtime.state.init_flow_step_state(child_runtime.path)

        if child_runtime.cancellation.is_cancelled(child_runtime.path):
            return

        child_runtime.checkpoint.set_started(child_runtime.path)

        try:
            runtime.terms.execute_term(child)
        except Exception as e:
            logger.exception(f"Error with term {child}")
            child_runtime.checkpoint.set_error(child_runtime.path, str(e))
        else:
            child_runtime.checkpoint.set_finished(child_runtime.path)

    # =========================================================================
    # Value Resolvers
    # =========================================================================

    def resolve(self, value: T | Sentinel | RValue[T | Sentinel], runtime: RuntimeT) -> T:
        """Resolve a value that may be an RValue.

        If value is an RValue (Term), executes it to get the actual value.
        Otherwise, returns the value as-is.

        Args:
            value: Either a plain value or an RValue/Term
            runtime: Current runtime for term execution

        Returns:
            The resolved value of type T
        """
        if isinstance(value, RValue):
            return runtime.terms.execute_term(value)
        return value

    def resolve_str(self, value: str | Sentinel | RValue[str | Sentinel], runtime: RuntimeT) -> str:
        """Resolve a string value that may be an RValue.

        Args:
            value: Either a plain string or an RValue returning string
            runtime: Current runtime

        Returns:
            The resolved string value
        """
        resolved = self.resolve(value, runtime)
        return str(resolved) if resolved is not None else ""

    def resolve_int(self, value: int | Sentinel | RValue[int | Sentinel], runtime: RuntimeT) -> int:
        """Resolve an int value that may be an RValue.

        Args:
            value: Either a plain int or an RValue returning int
            runtime: Current runtime

        Returns:
            The resolved int value
        """
        resolved = self.resolve(value, runtime)
        return int(resolved) if resolved is not None else 0

    def resolve_float(
        self,
        value: float | Sentinel | RValue[float | Sentinel],
        runtime: RuntimeT,
    ) -> float:
        """Resolve a float value that may be an RValue.

        Args:
            value: Either a plain float or an RValue returning float
            runtime: Current runtime

        Returns:
            The resolved float value
        """
        resolved = self.resolve(value, runtime)
        return float(resolved) if resolved is not None else 0.0

    def resolve_optional(
        self,
        value: T | Sentinel | RValue[T | Sentinel] | None,
        runtime: RuntimeT,
    ) -> T | None:
        """Resolve an optional value that may be an RValue.

        Args:
            value: Either a plain value, RValue, or None
            runtime: Current runtime

        Returns:
            The resolved value or None
        """
        if value is None:
            return None
        return self.resolve(value, runtime)

    # =========================================================================
    # Repr
    # =========================================================================

    def __repr__(self) -> str:
        cls_name = self.__class__.__name__
        return f"<{cls_name}>"

    def __str__(self) -> str:
        cls_name = self.__class__.__name__
        return f"{cls_name}"


def is_flow(obj: object) -> bool:
    """Check if object is a Flow."""
    return isinstance(obj, Flow)
