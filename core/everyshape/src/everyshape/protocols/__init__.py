"""View protocols — structural type contracts for storage/view objects.

Reactive protocols (what reactive morphisms check):
    ObservableProtocol              view.on_change()
    ChildObservableProtocol         view.on_child_change(address)
    ChildrenObservableProtocol      view.on_children_change()
    DescendantsObservableProtocol   view.on_descendents_change(*pattern)
"""

from everyshape.protocols.reactive import (
    ChildObservableProtocol,
    ChildrenObservableProtocol,
    DescendantsObservableProtocol,
    ObservableProtocol,
)


__all__ = [
    "ChildObservableProtocol",
    "ChildrenObservableProtocol",
    "DescendantsObservableProtocol",
    "ObservableProtocol",
]
