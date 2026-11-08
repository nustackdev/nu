"""A whole container write that keeps every declared view on the way down.

A view lays out the Python value it is handed by type: a ``dict`` child
becomes a plain dict, a ``list`` child a plain list. A Shape declares more
than that: an ordered, log or ring slot, or a ``view=`` on a slot. So a whole
row written through the parent view alone would land those slots in the wrong
layout, and nothing would say so.

``store_whole`` writes the value as the parent view would, then writes each
container child that needs its declared view through that view, all the way
down. The rows written are the same as one plain store: only the layout of
each child changes.
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING

from nu.domains.shape.mapping import MappingRef
from nu.domains.shape.shape import ShapeRef


if TYPE_CHECKING:
    from virtuals.view import ViewRegistry

    from .base import ViewRef


__all__ = [
    "store_whole",
]


def store_whole(parent: object, key: object, value: object, ref: ViewRef) -> None:
    """Write ``value`` whole at ``key`` under ``parent``, each container child in its declared view.

    Args:
        parent: the open, write-capable view holding the container.
        key: the container's address in ``parent``.
        value: the whole value, already lowered.
        ref: the container's ref, which declares its view and its children's.

    Raises:
        TypeError: ``ref`` is a list whose elements hold a container that
            needs its own view (a Shape with an ordered, log or ring slot):
            list elements are laid out by type only.
    """
    view_class = ref._payload["type_marker"]
    registry = parent.registry  # type: ignore[attr-defined]
    children = _laid_out_children(ref, value, registry)
    if not children:
        _refuse_list_of_laid_out(ref, value, registry)
        parent.set_child_container_as(key, value, view_class)  # type: ignore[attr-defined]
        return
    rest = {k: v for k, v in value.items() if k not in children}  # type: ignore[attr-defined]
    parent.set_child_container_as(key, rest, view_class)  # type: ignore[attr-defined]
    view = parent.open_child(key, view_class)  # type: ignore[attr-defined]
    for k, (child, v) in children.items():
        store_whole(view, k, v, child)


def _laid_out_children(
    ref: ViewRef, value: object, registry: ViewRegistry
) -> dict[object, tuple[ViewRef, object]]:
    """The container children of a mapping value to write one by one, or none.

    All of them or none: when one needs its declared view, every container
    child goes through its own write, in the value's order, so an ordered
    parent places its children as the value lists them.
    """
    from .base import ViewRef

    if not isinstance(ref, (ShapeRef, MappingRef)) or not isinstance(value, Mapping):
        return {}
    children: dict[object, tuple[ViewRef, object]] = {}
    for k, v in value.items():
        try:
            child = ref[k]
        except KeyError:
            continue  # not a declared slot: stored as the view lays it out
        if isinstance(child, ViewRef) and registry.is_container_type(v):
            children[k] = (child, v)
    if any(_needs_own_layout(child, v, registry) for child, v in children.values()):
        return children
    return {}


def _needs_own_layout(ref: ViewRef, value: object, registry: ViewRegistry) -> bool:
    """Whether laying ``value`` out by its type would miss what ``ref`` declares, here or below.

    ``value`` is a container type the registry knows, so it has a view to compare with.
    """
    declared = ref._payload["type_marker"]
    natural = registry.get_view_for_type(value.__class__)
    if natural.get_structure() != declared.get_structure():
        return True
    return bool(_laid_out_children(ref, value, registry)) or _list_of_laid_out(ref, value, registry)


def _list_of_laid_out(ref: ViewRef, value: object, registry: ViewRegistry) -> bool:
    """Whether ``ref`` is a list whose elements need a layout of their own."""
    from .base import ViewRef
    from .containers import ListRef

    if not isinstance(ref, ListRef) or not isinstance(value, (list, tuple)):
        return False
    element = ref[0]
    if not isinstance(element, ViewRef):
        return False
    return any(
        registry.is_container_type(v) and _needs_own_layout(element, v, registry) for v in value
    )


def _refuse_list_of_laid_out(ref: ViewRef, value: object, registry: ViewRegistry) -> None:
    if _list_of_laid_out(ref, value, registry):
        msg = (
            "a ListRef cannot be written whole when its elements hold an ordered, log or "
            "ring slot: they would lose that layout. Keep the rows in a DictRef or "
            "OrderedDictRef, or write each row's slots through their own refs"
        )
        raise TypeError(msg)
