"""Layer 3: Views - Data structure abstractions over containers.

Views provide familiar Python data structure interfaces (dict, list, set, etc.)
while delegating all storage operations to the Container API (Layer 2).

Core components:
- View: Base class for all views
- ViewRegistry: Type mapping between Python types and view classes
- Bases: Capability implementation bases for Views
- Capabilities and collections: Definitions for common capabilities of pythonic containers
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
from .capabilities import (
    Addable,
    Appendable,
    Assignable,
    ChildObservable,
    Clearable,
    Containable,
    Convertible,
    Deletable,
    DescendantsObservable,
    Discardable,
    Initializable,
    Insertable,
    Nestable,
    Observable,
    Poppable,
    Removable,
    Sizeable,
    Subscriptable,
    is_addable,
    is_appendable,
    is_assignable,
    is_child_observable,
    is_clearable,
    is_containable,
    is_convertible,
    is_deletable,
    is_descendants_observable,
    is_discardable,
    is_initializable,
    is_insertable,
    is_nestable,
    is_observable,
    is_poppable,
    is_removable,
    is_sizeable,
    is_subscriptable,
)
from .collections import (
    CollectionView,
    ContainerView,
    MappingView,
    MutableMappingView,
    MutableSequenceView,
    MutableSetView,
    SequenceView,
    SetView,
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
    # Capabilities
    "Addable",
    "Appendable",
    "Assignable",
    "ChildObservable",
    "Clearable",
    "Containable",
    "Convertible",
    "Deletable",
    "DescendantsObservable",
    "Discardable",
    "Initializable",
    "Insertable",
    "Nestable",
    "Observable",
    "Poppable",
    "Removable",
    "Sizeable",
    "Subscriptable",
    "is_addable",
    "is_appendable",
    "is_assignable",
    "is_child_observable",
    "is_clearable",
    "is_containable",
    "is_convertible",
    "is_deletable",
    "is_descendants_observable",
    "is_discardable",
    "is_initializable",
    "is_insertable",
    "is_nestable",
    "is_observable",
    "is_poppable",
    "is_removable",
    "is_sizeable",
    "is_subscriptable",
    # Collection protocols
    "CollectionView",
    "ContainerView",
    "MappingView",
    "MutableMappingView",
    "MutableSequenceView",
    "MutableSetView",
    "SequenceView",
    "SetView",
]
