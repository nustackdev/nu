"""Core type definitions.

Provides type aliases and shared data structures used across all layers.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING


if TYPE_CHECKING:
    from redwood.storage import StorageContextType
    from redwood.view import View


@dataclass(frozen=True)
class Context:
    """Execution context for operations and commands.

    Bundles together the tree instance and storage context needed
    for executing operations.

    Attributes:
        tree: Tree instance for navigation
        storage_context: Context for data access (transaction or snapshot)
    """

    root_view: View
    storage_context: StorageContextType
