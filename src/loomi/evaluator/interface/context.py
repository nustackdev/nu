from __future__ import annotations

from typing import Any, Protocol

from .type_vars import OperationT_co, StateT_co

__all__ = [
    "ContextProtocol",
]


class ContextProtocol(Protocol[OperationT_co, StateT_co]):
    """
    Protocol defining the interface for a context.
    Contexts provide access to state and services during operation execution.
    """

    # --- Properties access methods --- #

    @property
    def scope(self) -> "StateT_co":
        """
        Get the scoped state access.

        Returns:
            The scoped state access.
        """
        ...

    @property
    def operation(self) -> OperationT_co:
        """
        Get the operation associated with context.

        Returns:
            The operation.
        """
        ...

    # --- Context attributes access methods --- #

    def __getitem__(self, key: str) -> Any:
        """
        Get an attribute by key.

        Args:
            key: Attribute key

        Returns:
            Attribute value
        """
        ...

    def __setitem__(self, key: str, value: Any) -> None:
        """
        Set an attribute by key.

        Args:
            key: Attribute key
            value: Attribute value
        """
        ...

    def __contains__(self, key: str) -> bool:
        """
        Check if an attribute exists.

        Args:
            key: Attribute key

        Returns:
            True if the attribute exists, False otherwise
        """
        ...

    def __delitem__(self, key: str) -> None:
        """
        Delete an attribute by key.

        Args:
            key: Attribute key
        """
        ...
