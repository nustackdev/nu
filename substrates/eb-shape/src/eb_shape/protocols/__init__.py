"""View protocols — structural type contracts for storage/view objects.

Collection protocols (what collection morphisms check):
    ExtractableProtocol     view.extract()
    StorableProtocol        view.store(data)
    ClearableProtocol       view.clear()

Reactive protocols (what reactive morphisms check):
    ObservableProtocol              view.on_change()
    ChildObservableProtocol         view.on_child_change(address)
    ChildrenObservableProtocol      view.on_children_change()
    DescendantsObservableProtocol   view.on_descendents_change(*pattern)
"""

from eb_shape.protocols.collection import (
    ClearableProtocol,
    ExtractableProtocol,
    StorableProtocol,
)
from eb_shape.protocols.reactive import (
    ChildObservableProtocol,
    ChildrenObservableProtocol,
    DescendantsObservableProtocol,
    ObservableProtocol,
)


__all__ = [
    "ChildObservableProtocol",
    "ChildrenObservableProtocol",
    "ClearableProtocol",
    "DescendantsObservableProtocol",
    "ExtractableProtocol",
    "ObservableProtocol",
    "StorableProtocol",
]
