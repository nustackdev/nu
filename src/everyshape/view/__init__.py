"""Layer 3: Views - Data structure abstractions over containers.

Views provide familiar Python data structure interfaces (dict, list, set, etc.)
while delegating all storage operations to the Container API (Layer 2).

Core components:
- View: Base class for all views
- ViewRegistry: Type mapping between Python types and view classes
- Built-in views: DictView, ListView, SetView, etc.

Example:
    >>> from everyshape.view import View, ViewRegistry
    >>> from everyshape.tree import Container, ContainerStructure, ContainerProtocol
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

from .base import ViewBase
from .bases import (
    ChildNavigationBase,
    ChildNestedGetBase,
    ChildNestedSetBase,
    LiveChildrenCountBase,
    MetadataBasedChildrenCountBase,
)
from .bases_observable import (
    ChildObservableBase,
    DescendantsObservableBase,
    ObservableBase,
)
from .exceptions import RegistryError, ViewError, ViewOperationError
from .registry import ViewRegistry
from .view import View


__all__ = [
    "ChildNavigationBase",
    "ChildNestedGetBase",
    "ChildNestedSetBase",
    "ChildObservableBase",
    "DescendantsObservableBase",
    "LiveChildrenCountBase",
    "MetadataBasedChildrenCountBase",
    "ObservableBase",
    "RegistryError",
    "View",
    "ViewBase",
    "ViewError",
    "ViewOperationError",
    "ViewRegistry",
]
