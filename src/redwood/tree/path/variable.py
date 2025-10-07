"""
Path variable storage and interface design.

This module focuses on how to store variables in path data and provide
a clean interface for variable creation and usage.
"""

from __future__ import annotations

from typing import Any

import attrs


__all__ = ["Variable"]


@attrs.define(frozen=True, slots=True)
class Variable:
    """
    Represents a variable reference in a path that needs runtime resolution.

    Variables can be:
    - Simple: Variable("user_id") -> resolves to variables["user_id"]
    - Nested: Variable("user", "profile", "id") -> resolves to variables["user"]["profile"]["id"]

    The nested approach using *path makes it more explicit and allows for
    better error handling and type checking.
    """

    path: tuple[str | int, ...] = attrs.field()

    def resolve(self, vars: dict[str | int, Any]) -> Any:
        """
        Resolve the variable path against the provided vars dictionary.

        Args:
            vars: Dictionary containing variable values

        Returns:
            Resolved value from vars

        Raises:
            KeyError: If any part of the variable path is not found
            TypeError: If trying to access attribute on non-dict value
        """
        current = vars
        for i, component in enumerate(self.path):
            if not isinstance(current, (dict, list, tuple)):
                path_so_far = ".".join([str(p) for p in self.path[:i]])
                raise TypeError(
                    f"Cannot access '{component}' on {type(current).__name__} "
                    f"at variable path '{path_so_far}'"
                )
            if component not in current:
                available_keys = list(current.keys()) if isinstance(current, dict) else []
                raise KeyError(
                    f"Variable component '{component}' not found in variables. "
                    f"Available keys: {available_keys}"
                )

            if isinstance(current, dict):
                current = current[component]
            elif isinstance(current, (list, tuple)):
                try:
                    component = int(component)  # Convert to int for list access
                except ValueError:
                    raise KeyError(
                        f"Invalid index '{component}' for list at variable path "
                        f"{'.'.join([str(p) for p in self.path[:i]])}"
                    )
        return current

    def __str__(self) -> str:
        """String representation showing the variable path."""
        return f"${'.'.join([str(p) for p in self.path])}"

    def __repr__(self) -> str:
        """Detailed representation for debugging."""
        if len(self.path) == 1:
            return f"Variable('{self.path[0]}')"
        return f"Variable({', '.join(repr(p) for p in self.path)})"
