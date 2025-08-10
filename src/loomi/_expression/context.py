"""
Updated Context class with structural path support.

Provides execution context with hierarchical structural identification
for deterministic and resumable expression execution.
"""

from __future__ import annotations

from copy import deepcopy
from typing import Any

import attrs
from frozendict import frozendict

from .exceptions import ContextError
from .logger import logger
from .structural_path import StructuralPath

__all__ = ["Context"]


@attrs.define(frozen=True, slots=True)
class Context:
    """
    Execution context for expressions with structural path support.

    Provides expressions with access to attributes and hierarchical
    structural identification for deterministic execution tracking.
    """

    attributes: frozendict[str, Any] = attrs.field(factory=frozendict)
    structural_path: StructuralPath = attrs.field(factory=StructuralPath)

    # --- Context attributes access methods --- #

    def __getitem__(self, key: str) -> Any:
        """
        Get an attribute by key.

        Args:
            key: Attribute key

        Returns:
            Attribute value

        Raises:
            ContextError: If the key is not found in the context attributes
        """
        try:
            value = self.attributes[key]
            logger.debug(
                "Retrieved context attribute",
                extra={
                    "key": key,
                    "value_type": type(value).__name__,
                    "structural_path": str(self.structural_path),
                },
            )
            return value
        except KeyError as e:
            logger.error(
                "Context attribute not found",
                extra={
                    "key": key,
                    "available_keys": list(self.attributes.keys()),
                    "structural_path": str(self.structural_path),
                },
            )
            raise ContextError(f"Context attribute '{key}' not found") from e

    def __contains__(self, key: str) -> bool:
        """
        Check if an attribute exists.

        Args:
            key: Attribute key

        Returns:
            True if the attribute exists, False otherwise
        """
        return key in self.attributes

    # --- Structural path properties --- #

    @property
    def structural_key(self) -> tuple[str, ...]:
        """Get the storage key for this structural path."""
        return self.structural_path.components

    @property
    def is_root_context(self) -> bool:
        """Check if this is a root execution context."""
        return self.structural_path.is_root

    # --- Context creation methods --- #

    def derive(
        self,
        attributes: dict | frozendict | None = None,
        structural_path: StructuralPath | None = None,
    ) -> Context:
        """
        Create a new context derived from this one.

        Used to create contexts for child expressions, extending structural paths
        and optionally updating attributes.

        Args:
            attributes: New attributes to merge with existing ones
            structural_path: New structural path (if not provided, inherits parent's)

        Returns:
            A new context derived from this one

        Raises:
            ContextError: If context derivation fails
        """
        logger.debug(
            "Deriving new context",
            extra={
                "has_new_attributes": attributes is not None,
                "parent_attributes_count": len(self.attributes),
                "parent_structural_path": str(self.structural_path),
                "new_structural_path": str(structural_path) if structural_path else None,
            },
        )

        try:
            # Start with current values
            values = {
                "attributes": deepcopy(self.attributes),
                "structural_path": self.structural_path,
            }

            updates: dict[str, Any] = {}

            # Merge attributes if provided
            if attributes is not None:
                merged_attributes = {**values["attributes"], **attributes}
                updates["attributes"] = frozendict(merged_attributes)

            # Update structural path if provided
            if structural_path is not None:
                updates["structural_path"] = structural_path

            values.update(updates)

            # Create new context
            new_context = self.__class__(**values)

            logger.debug(
                "Successfully derived new context",
                extra={
                    "new_attributes_count": len(new_context.attributes),
                    "new_structural_path": str(new_context.structural_path),
                },
            )

            return new_context

        except Exception as e:
            logger.error(
                "Failed to derive context",
                extra={
                    "error_type": type(e).__name__,
                    "error_message": str(e),
                    "parent_structural_path": str(self.structural_path),
                },
                exc_info=True,
            )
            raise ContextError(f"Failed to derive context: {e}") from e

    def create_child_context(
        self,
        child_component: str,
        attributes: dict | frozendict | None = None,
    ) -> Context:
        """
        Create a child context with extended structural path.

        This is a convenience method for creating child contexts with
        automatically extended structural paths.

        Args:
            child_component: Component to append to structural path
            attributes: Additional attributes for the child context

        Returns:
            A new child context with extended structural path
        """
        child_structural_path = self.structural_path.append(child_component)
        return self.derive(
            attributes=attributes,
            structural_path=child_structural_path,
        )
