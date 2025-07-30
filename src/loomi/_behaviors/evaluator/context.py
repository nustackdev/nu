"""
Runtime context for expressions execution.

This module defines the Context class, which provides expressions
with access to state, services, and execution metadata.
"""

from __future__ import annotations

from copy import deepcopy
from typing import TYPE_CHECKING, Any

import attrs
from frozendict import frozendict

from .exceptions import ContextError
from .logger import logger

if TYPE_CHECKING:
    from .expression import Expression


@attrs.define(frozen=True, slots=True)
class Context:
    """
    Execution context for expressions.

    Provides expressions with access to state, execution service, and structured path data.
    This is the primary interface through which expressions interact with their environment.
    """

    expression: "Expression"  # The expression this context is associated with
    attributes: frozendict[str, Any] = attrs.field(factory=frozendict)  # Context attributes storage

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
                    "context_id": id(self),
                },
            )
            return value
        except KeyError as e:
            logger.error(
                "Context attribute not found",
                extra={
                    "key": key,
                    "available_keys": list(self.attributes.keys()),
                    "context_id": id(self),
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

    # --- Context creation methods --- #

    def derive(
        self,
        expression: Expression | None = None,
        attributes: frozendict | None = None,
    ) -> Context:
        """
        Create a new context derived from this one.

        Used to create contexts for child expressions, extending structural paths
        and optionally updating other properties.

        Args:
            expression: New expression to associate with the context
            attributes: New attributes to merge with existing ones

        Returns:
            A new context derived from this one

        Raises:
            ContextError: If context derivation fails
        """
        logger.debug(
            "Deriving new context",
            extra={
                "parent_expression_type": type(self.expression).__name__,
                "new_expression_type": type(expression).__name__ if expression else None,
                "has_new_attributes": attributes is not None,
                "parent_attributes_count": len(self.attributes),
            },
        )

        try:
            # Start with current values
            values = {
                "expression": self.expression,
                "attributes": deepcopy(self.attributes),
            }

            updates: dict[str, Any] = {}

            # Update expression if provided
            if expression is not None:
                updates["expression"] = expression

            # Merge attributes if provided
            if attributes is not None:
                # Merge the new attributes with existing ones
                # TODO: implement deep merge (?)
                merged_attributes = {**values["attributes"], **attributes}
                updates["attributes"] = frozendict(merged_attributes)

            values.update(updates)

            # Create new context
            new_context = self.__class__(**values)

            logger.debug(
                "Successfully derived new context",
                extra={
                    "new_expression_type": type(new_context.expression).__name__,
                    "new_attributes_count": len(new_context.attributes),
                },
            )

            return new_context

        except Exception as e:
            logger.error(
                "Failed to derive context",
                extra={
                    "error_type": type(e).__name__,
                    "error_message": str(e),
                },
                exc_info=True,
            )
            raise ContextError(f"Failed to derive context: {e}") from e
