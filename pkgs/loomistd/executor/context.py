from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, List, Optional, Union

if TYPE_CHECKING:
    from loomi.app.handlers.state import AsyncStateDictProtocol

    from .services.tracing import TracingService


@dataclass(frozen=True)
class RuntimeContext:
    """
    Execution context for operations.

    Provides operations with access to state, services, and execution metadata.
    This is the primary interface through which operations interact with
    their environment.
    """

    # Execution path for this context
    path: List[str]

    # State access
    state: "AsyncStateDictProtocol"

    # Execution metadata (for collection operations)
    key: Optional[Union[str, int]] = None
    index: Optional[int] = None

    # Services
    tracing: "TracingService | None" = None
    # other services ...

    # Parent context reference
    parent: Optional["RuntimeContext"] = None

    def derive(self, **updates) -> "RuntimeContext":
        """
        Create a new context derived from this one.

        Used to create contexts for child operations, extending the execution path
        and optionally updating other properties.

        Args:
            **updates: Attributes to update in the new context

        Returns:
            A new context derived from this one
        """
        # Start with current values
        values = {
            "path": list(self.path),
            "state": self.state,
            "key": self.key,
            "index": self.index,
            "tracing": self.tracing,
            "parent": self,
        }

        # Apply updates
        values.update(updates)

        # Create new context
        return RuntimeContext(**values)

    def extend_path(self, *components: str) -> "RuntimeContext":
        """
        Create a new context with an extended path.

        This is a convenience method for deriving a context with a path
        extended by the given components.

        Args:
            *components: Path components to append

        Returns:
            A new context with the extended path
        """
        new_path = list(self.path)
        new_path.extend(components)
        return self.derive(path=new_path)
