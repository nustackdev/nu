"""``ContainerRef`` -- the base every layout container Ref builds on.

Layer 1. A container Ref is a whole container on its own: it needs no Shape
to draw, to carry chrome or to hold children.

- **Children** come from ``parent_ref=``: ``TextRef("t", parent_ref=row)``
  puts a text in ``row``. Navigating a Shape whose ``_ref_cls`` is this Ref
  (``page.toolbar.text``) reaches the same place by way of its slots.
- **Repetition is free.** The address is a term, so computed keys under one
  parent (``RowRef(nu.Str("r") + nu.str(i), parent_ref=col)``) are as many
  distinct children as there are keys, with nothing declared up front.
- **Props** ride ``props=`` on the constructor, or ``slot(**props)`` when the
  Ref is declared on a Shape; both go through this class's own ``slot()``,
  so the defaults and normalization live here and nowhere else.
- **No ``set()``** unless one chrome value is the thing the container
  carries (Modal: open). The rest of its chrome is ``set_*``. ``ListRef``
  keeps its old string ``set(items)`` for compatibility.
- **How it holds children** is the container's kind, one per class, the way
  kv has ``ShapeRef``, ``DictRef`` and ``ListRef``. A ``DictContainerRef``
  takes children by key, a ``ListContainerRef`` by index, and a
  ``ShapeContainerRef`` only the ones its Shape declares. The first two may
  carry an item template, ``slot(Item)`` or ``item=Item``, and ``ref[key]``
  answers with an ``Item`` there, the way ``DictRef.slot(Order)`` answers
  ``desks["d1"]`` with an Order. Declared slots are keys too, so named and
  templated children mix. There are no collection ops: a UI child is a
  component, not a value, so the kind only says how a child is reached.

The parent's flow decides how a child displays: the same Badge is a block in
a Column, a cell in a Grid and a run of text in a Line. A child never says.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, ClassVar

from typing_extensions import Self

from nu.lang import Nu
from nustd.ui.core import Ref, Section, SectionRef


if TYPE_CHECKING:
    from collections.abc import Mapping


__all__ = ["ContainerRef", "DictContainerRef", "ListContainerRef", "ShapeContainerRef"]


class ContainerRef(SectionRef):
    """Base for container Refs: open-ended children, optional chrome. Abstract.

    Something is a container only when its children are open-ended user
    composition. Fixed known parts (a button's label and icon) are props on
    a leaf instead.
    """

    # Abstract: never on the wire. Every concrete container declares its own.
    _wire_type: ClassVar[str] = ""


class _ItemContainerRef(ContainerRef):
    """A container whose children may come from one item template. Abstract.

    The template is a Section class or a Ref class. It rides the payload, as
    ``section_cls`` does, so it survives a tree rewrite, and ``ref[key]``
    reads it there to build the child. No class is made for it.
    """

    _takes_item: ClassVar[bool] = True

    def __init__(
        self,
        address: object,
        *,
        item: type[Section] | type[Ref] | None = None,
        section_cls: type[Section] | None = None,
        parent_ref: Ref | None = None,
        owner_shape: type[Section] | None = None,
        props: Mapping[str, object] | None = None,
    ) -> None:
        super().__init__(
            address,
            section_cls=section_cls,
            parent_ref=parent_ref,
            owner_shape=owner_shape,
            props=props,
        )
        self._payload["item"] = _checked_item(type(self), item)

    @classmethod
    def slot(cls, item: type[Section] | type[Ref] | None = None, /, **props: object) -> Self:
        """Declare this container as a slot, its children drawn from ``item``."""
        declared = super().slot(**props)
        if item is not None:
            declared.kwargs["item"] = _checked_item(cls, item)  # type: ignore[attr-defined]
        return declared

    def _item_child(self, key: object) -> Ref:
        item = self._payload.get("item")
        section_cls = self._payload.get("section_cls")
        if item is None:
            owner = (section_cls or type(self)).__name__
            msg = (
                f"{owner} has no item template to build ref[{key!r}] from; declare"
                f" one with .slot(Item), or build children as Refs with parent_ref="
            )
            raise TypeError(msg)
        slot = item.slot()
        ref = slot.ref_cls(key, owner_shape=section_cls, parent_ref=self, **slot.kwargs)
        if slot.props:
            ref._payload["props"] = dict(slot.props)
        return ref


class DictContainerRef(_ItemContainerRef):
    """A container that takes its children by key. Abstract.

    ``ref[key]`` is the item template's child at ``key``. The key is a term
    like any address, so a computed key works too.
    """

    def __getitem__(self, key: object) -> Ref:
        return self._item_child(key)


class ListContainerRef(_ItemContainerRef):
    """A container that takes its children by position. Abstract.

    ``ref[i]`` is the item template's child at index ``i``, an int or an
    int term. The browser draws indexed children in index order.
    """

    def __getitem__(self, index: object) -> Ref:
        if isinstance(index, bool) or not isinstance(index, (int, Nu)):
            msg = f"{type(self).__name__} indices are ints, not {type(index).__name__}"
            raise TypeError(msg)
        if isinstance(index, int) and index < 0:
            msg = f"{type(self).__name__} has no length to count back from; use an index >= 0"
            raise IndexError(msg)
        return self._item_child(index)


class ShapeContainerRef(ContainerRef):
    """A container whose children are only the ones its Shape declares. Abstract.

    It takes no item template and cannot be subscripted.
    """


def _checked_item(owner: type, item: object) -> type[Section] | type[Ref] | None:
    if item is None or (
        isinstance(item, type) and issubclass(item, (Section, Ref)) and item is not Section
    ):
        return item  # type: ignore[return-value]
    msg = f"{owner.__name__} item must be a Section or a Ref class, not {item!r}"
    raise TypeError(msg)
