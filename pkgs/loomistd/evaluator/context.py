"""
Runtime context for expressions execution.

This module defines the Context class, which provides expressions
with access to state, services, and execution metadata.
"""

from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any, Generic

from loomi.evaluator.interface.context import ContextProtocol
from loomi.state.interface.tree import AsyncStateProtocol, SyncStateProtocol
from loomi.state.interface.type_vars import StateT

if TYPE_CHECKING:
    from .expressions.base import Expression


@dataclass
class Context(Generic[StateT]):
    """
    Execution context for expressions.

    Provides expressions with access to state, execution service, and structured path data.
    This is the primary interface through which expressions interact with their environment.

    """

    _expression: "Expression"  # The expression this context is associated with
    _scope: StateT  # The scoped state access
    _attributes: dict[str, Any] = field(default_factory=dict)  # Context attributes storage

    @property
    def operation(self) -> "Expression":
        # TODO: added temporary property for compatibility with older interfaces
        return self._expression

    # --- Properties access methods --- #
    @property
    def expression(self) -> "Expression":
        """
        Get the current expression.

        Returns:
            The current expression.
        """
        return self._expression

    @property
    def scope(self) -> StateT:
        """
        Get the scoped state access.

        Returns:
            The scoped state access.
        """
        return self._scope

    # --- Context attributes access methods --- #

    def __getitem__(self, key: str) -> Any:
        """
        Get an attribute by key.

        Args:
            key: Attribute key

        Returns:
            Attribute value
        """
        return self._attributes[key]

    def __setitem__(self, key: str, value: Any) -> None:
        """
        Set an attribute by key.

        Args:
            key: Attribute key
            value: Attribute value
        """
        self._attributes[key] = value

    def __contains__(self, key: str) -> bool:
        """
        Check if an attribute exists.

        Args:
            key: Attribute key

        Returns:
            True if the attribute exists, False otherwise
        """
        return key in self._attributes

    def __delitem__(self, key: str) -> None:
        """
        Delete an attribute by key.

        Args:
            key: Attribute key
        """
        del self._attributes[key]

    # --- Context creation methods --- #

    def derive(
        self,
        expression: Expression | None = None,
        scope: "AsyncStateProtocol | SyncStateProtocol | None" = None,
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
            "_expression": self._expression,
            "_scope": self._scope,
            "_attributes": deepcopy(self._attributes),
        }

        updates: dict[str, Any] = {}

        if expression is not None:
            updates["_expression"] = expression

        if scope is not None:
            updates["_scope"] = scope

        values.update(updates)

        # Create new context
        return self.__class__(**values)


if TYPE_CHECKING:
    _: type[ContextProtocol["Expression", Any]] = Context
