"""
Runtime context for operations execution.

This module defines the Context class, which provides operations
with access to state, services, and execution metadata.
"""

from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any, Dict, Tuple

if TYPE_CHECKING:
    from loomi.app.state import AsyncStateProtocol
    from loomi.app.state.protocols import AsyncStateDictProtocol
    from loomi.app.tasks.protocols import ContextProtocol

    from .services.task_execution import TaskExecutionService
    from .services.tracing import TracingService


@dataclass
class Context(ContextProtocol):
    """
    Execution context for operations.

    Provides operations with access to state, execution service, and structured path data.
    This is the primary interface through which operations interact with their environment.

    """

    # Services
    state: "AsyncStateProtocol"
    executor: "TaskExecutionService"
    tracing: "TracingService"
    scoped: "AsyncStateDictProtocol"  # Scoped state access

    # Identities
    structural_path: Tuple[str, ...]  # Structural path - represents position in operation tree
    state_path: Tuple[str, ...]  # State path - represents position in state tree

    # Attributes
    attributes: Dict[str, Any] = field(default_factory=dict)

    def derive(self, **updates: Any) -> "Context":
        """
        Create a new context derived from this one.

        Used to create contexts for child operations, extending structural paths
        and optionally updating other properties.

        Args:
            **updates: Attributes to update in the new context

        Returns:
            A new context derived from this one
        """
        # Start with current values
        values = {
            "state": self.state,
            "executor": self.executor,
            "tracing": self.tracing,
            "scoped": self.scoped,
            "structural_path": self.structural_path,
            "state_path": self.state_path,
        }

        # Apply updates
        values.update(updates)

        # Create new context
        return Context(**values)

    def with_structural_path(self, *components: str) -> "Context":
        """
        Create a new context with an extended structural path.

        Args:
            *components: Path components to append

        Returns:
            A new context with the extended structural path
        """
        new_path = self.structural_path + components
        return self.derive(structural_path=new_path)

    def with_state_path(self, *components: str) -> "Context":
        """
        Create a new context with an extended state path.

        Args:
            *components: Path components to append

        Returns:
            A new context with the extended state path
        """
        new_path = self.state_path + components
        return self.derive(state_path=new_path)

    def set_attribute(self, key: str, value: Any) -> None:
        """
        Set a context attribute.

        Args:
            key: Attribute key
            value: Attribute value
        """
        self.attributes[key] = value

    def get_attribute(self, key: str, default: Any = None) -> Any:
        """
        Get a context attribute.

        Args:
            key: Attribute key
            default: Default value if not found

        Returns:
            Attribute value or default
        """
        return self.attributes.get(key, default)

    def get_structural_path_str(self) -> str:
        """
        Get the structural path as a string.

        Returns:
            Structural path joined with dots
        """
        return ".".join(str(component) for component in self.structural_path)

    def get_state_path_str(self) -> str:
        """
        Get the state path as a string.

        Returns:
            State path joined with dots, or structural path if state_path is None
        """
        return ".".join(str(component) for component in self.state_path)
