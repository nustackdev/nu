"""KV Context."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

import attrs

from every import Context


if TYPE_CHECKING:
    from pv.storage import StorageContextType
    from pv.view import View

    from every import Shape

__all__ = [
    "KVContext",
]

logger = logging.getLogger(__name__)


@attrs.frozen
class SingularContext:
    """Execution context for operations and commands.

    Bundles together the tree instance and storage context needed
    for executing operations.

    Attributes:
        tree: Tree instance for navigation
        storage_context: Context for data access (transaction, snapshot or write batch)
    """

    root_view: View
    storage_context: StorageContextType


@attrs.frozen
class KVContext(Context):
    """Mutlic-context execution.

    The default execution context for EveryBase Terms.
    """

    default_context: SingularContext
    contexts: dict[type[Shape], SingularContext] = attrs.field(factory=dict)

    @classmethod
    def create(
        cls,
        root_view: View,
        storage_context: StorageContextType,
        contexts: dict[type[Shape], tuple[View, StorageContextType]] | None = None,
    ) -> KVContext:
        """Creates new context instance."""
        return cls(
            default_context=SingularContext(root_view, storage_context),
            contexts={
                s: SingularContext(context[0], context[1])
                for s, context in (contexts or {}).items()
            },
        )

    def get_context_for_shape(self, shape_type: type[Shape] | None) -> SingularContext:
        """Get context for a given Shape."""
        if shape_type is None:
            logger.debug("shape_type is None, using default context.")
            return self.default_context

        try:
            return self.contexts[shape_type]
        except KeyError:
            logger.debug(
                f"Context not found for Shape {shape_type.__name__}, using default context."
            )
            return self.default_context
