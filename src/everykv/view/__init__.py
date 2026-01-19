"""Layer 3: Views - Data structure abstractions over containers.

Views provide familiar Python data structure interfaces (dict, list, set, etc.)
while delegating all storage operations to the Container API (Layer 2).

Core components:
- View: Base class for all views
- ViewRegistry: Type mapping between Python types and view classes
- Bases: Capability implementation bases for Views
"""

from __future__ import annotations

from .bases import (
    ChildNavigationBase,
    ChildNestedGetBase,
    ChildNestedSetBase,
    ChildObservableBase,
    DescendantsObservableBase,
    LiveChildrenCountBase,
    MetadataBasedChildrenCountBase,
    ObservableBase,
    ViewBase,
)
from .exceptions import ViewError, ViewOperationError, ViewRegistryError
from .registry import ViewRegistry
from .view import View


__all__ = [  # noqa: RUF022
    "ChildNavigationBase",
    "ChildNestedGetBase",
    "ChildNestedSetBase",
    "ChildObservableBase",
    "DescendantsObservableBase",
    "LiveChildrenCountBase",
    "MetadataBasedChildrenCountBase",
    "ObservableBase",
    "ViewRegistryError",
    "View",
    "ViewBase",
    "ViewError",
    "ViewOperationError",
    "ViewRegistry",
]
