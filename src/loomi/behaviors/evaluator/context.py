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

if TYPE_CHECKING:
    from .expressions import Expression


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
        """
        return self.attributes[key]

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
            scope: New scope to use for state access

        Returns:
            A new context derived from this one
        """
        values = {
            "expression": self.expression,
            "attributes": deepcopy(self.attributes),
        }

        updates: dict[str, Any] = {}

        if expression is not None:
            updates["expression"] = expression

        values.update(updates)

        # Create new context
        return self.__class__(**values)
