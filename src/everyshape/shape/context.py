"""Terms execution context defintion."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, Protocol


if TYPE_CHECKING:
    from .shape import Shape


__all__ = [
    "ContextProtocol",
]


@dataclass(frozen=True)
class ContextProtocol(Protocol):
    """Execution context for operations and commands.

    Bundles together the tree instance and storage context needed for executing operations.

    """

    def get_context_for_shape(self, shape_type: type[Shape] | None) -> Any:  # noqa: ANN401
        """Get context for shape."""
        ...
