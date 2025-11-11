"""Layer 3: Views - Data structure abstractions over containers.

Views provide familiar Python data structure interfaces (dict, list, set, etc.)
while delegating all storage operations to the Container API (Layer 2).

Core components:
- View: Base class for all views
- ViewRegistry: Type mapping between Python types and view classes
- Built-in views: DictView, ListView, SetView, etc.

Example:
    >>> from redwood.view import View, ViewRegistry
    >>> from redwood.tree import Container, ContainerStructure, ContainerProtocol
    >>> registry = ViewRegistry()
    >>> registry.register_builtin_views()
    >>> with storage.transaction() as tx:
    ...     container = Container.create(
    ...         path=("users",),
    ...         ctx=tx,
    ...         structure=ContainerStructure(1),
    ...         protocol=ContainerProtocol.MUTABLE,
    ...     )
    ...     users = DictView(container, registry)
    ...     users["alice"] = {"name": "Alice"}
"""

from __future__ import annotations

from .exceptions import RegistryError, ViewError, ViewOperationError
from .navigation import (
    build_value_path,
    build_view_path,
    last_segment,
    navigate_value,
    navigate_view,
    open_child_view,
    open_parent_view,
    parent_view_path,
    split_value_path,
)
from .registry import ViewRegistry
from .types import (
    ValuePath,
    ValueSegment,
    ViewKey,
    ViewPath,
    ViewSegment,
)
from .view import View


__all__ = [  # noqa: RUF022
    # Main types
    "RegistryError",
    "View",
    # Errors
    "ViewError",
    "ViewOperationError",
    "ViewRegistry",
    # Types
    "ValuePath",
    "ValueSegment",
    "ViewKey",
    "ViewPath",
    "ViewSegment",
    # Navigation
    "build_view_path",
    "build_value_path",
    "split_value_path",
    "parent_view_path",
    "last_segment",
    "open_child_view",
    "navigate_view",
    "navigate_value",
    "open_parent_view",
]
