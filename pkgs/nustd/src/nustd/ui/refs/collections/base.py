"""``CollectionRef`` -- the base every Ref that holds children builds on.

The counterpart of ``LeafRef``: a leaf draws from its props and never holds
children, a collection holds open-ended ones. Layer 1. A collection Ref is a
whole container on its own: it needs no Shape to draw, to carry chrome or to
hold children. (``ContainerRef`` is one of them, the page frame.)

- **Children** come from ``parent_ref=``: ``TextRef("t", parent_ref=row)``
  puts a text in ``row``. Navigating a Shape whose ``_ref_cls`` is this Ref
  (``page.toolbar.text``) reaches the same place by way of its slots.
- **Repetition is free.** The address is a term, so computed keys under one
  parent (``RowRef(nu.Str("r") + nu.str(i), parent_ref=col)``) are as many
  distinct children as there are keys, with nothing declared up front.
- **Props** ride ``props=`` on the constructor, or ``slot(**props)`` when the
  Ref is declared on a Shape; both go through this class's own ``slot()``,
  so the defaults and normalization live here and nowhere else.
- **No ``set()``** unless one value is the thing the container carries
  (Modal: open, List: its string items). The rest of its chrome is
  ``set_*``, its own layout ``set_layout``, a child's ``set_child`` (see
  ``layout``).
- **Descent** is the container's own. A ``DictCollectionRef`` takes
  ``ref[0]`` (a position) and ``ref["k"]`` (a name), a ``ListCollectionRef``
  positions only, a ``ShapeCollectionRef`` none (its parts are properties).
  Named parts (``card.actions``) are properties with a default kind. The
  child at a key is a bare ``ItemRef`` (``.to(Kind)`` names the kind where
  it is used) unless the container has a default, ``slot(Item)`` or
  ``item=Item``, where ``Item`` is a class or a ``Kind.slot(**props)`` spec.
  Declared slots are reached by attribute, not by key. There are no
  collection ops: a UI child is a component, not a value, so the kind only
  says how a child is reached.

The parent's flow decides how a child displays: the same Badge is a block in
a Column, a cell in a Grid and a run of text in a Line. A child never says.
How each container sizes, spaces and arranges is the four layers of
``layout``, the same words on every one.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, ClassVar

from typing_extensions import Self

from nustd.ui.core import ItemRef, Ref, Section, SectionRef, as_spec, check_key, child_at

from .layout import SIZE, Laid, layout_props, same_place


if TYPE_CHECKING:
    from collections.abc import Mapping

    from nu.domains.shape import Slot

    from .layout import Check


__all__ = ["CollectionRef", "DictCollectionRef", "ListCollectionRef", "ShapeCollectionRef"]


class CollectionRef(SectionRef):
    """Base for collection Refs: open-ended children, optional chrome. Abstract.

    Something is a container only when its children are open-ended user
    composition. Fixed known parts (a button's label and icon) are props on
    a leaf instead.
    """

    # Abstract: never on the wire. Every concrete container declares its own.
    _wire_type: ClassVar[str] = ""

    # Names this container places itself and answers by property (a Card's
    # ``media``, ``actions``, ``footer``). A Shape may declare a slot of such
    # a name, since the property answers with it; ``ref[name]`` is refused.
    _parts: ClassVar[frozenset[str]] = frozenset()

    # Which keys a child takes: positions (int keys) and names (str keys).
    _positions: ClassVar[bool] = True
    _names: ClassVar[bool] = True

    # The layout this container speaks (see ``layout``): its layer props, its
    # family and surface props (name to check), the per child maps it keeps,
    # and the words its arrange props take.
    _layout: ClassVar[frozenset[str]] = SIZE
    _family: ClassVar[Mapping[str, Check]] = {}
    _children: ClassVar[tuple[str, ...]] = ()
    _justifies: ClassVar[tuple[str, ...]] = ("start", "center", "end", "between")
    _aligns: ClassVar[tuple[str, ...]] = ("start", "center", "end", "stretch")
    _self_aligns: ClassVar[tuple[str, ...]] = ("start", "center", "end", "stretch")
    _sticky_sides: ClassVar[tuple[str, ...]] = ("top", "bottom")

    @classmethod
    def _laid_out(cls, given: Mapping[str, object], **context: object) -> dict[str, object]:
        """The layout props in ``given`` that are set, checked (see ``layout_props``)."""
        return layout_props(cls, given, **context)

    @classmethod
    def _child_key(cls, key: object, **_: object) -> str:
        """A per child map key as the wire carries it: the child's segment text."""
        check_key(cls.__name__, key, positions=cls._positions, names=cls._names, parts=cls._parts)
        if isinstance(key, Ref) or not isinstance(key, int | str):
            msg = f"{cls.__name__} per child maps on slot() take plain keys, not {key!r}"
            raise TypeError(msg)
        return str(key)

    def _child_runtime_key(self, key: object) -> object:
        """A ``set_child`` key: checked like a descent, a term passes as given."""
        owner = self._owner_name()
        check_key(owner, key, positions=self._positions, names=self._names, parts=self._parts)
        return key

    def _key_of_child(self, child: Ref) -> object:
        """The key ``child`` sits at under this container; a child of another one fails loud."""
        if not same_place(child._parent, self):
            msg = f"{self._owner_name()} takes a child of its own or a key, not {child!r}"
            raise ValueError(msg)
        return child._payload["segment"]

    def _owner_name(self) -> str:
        section_cls = self._payload.get("section_cls")
        return (section_cls or type(self)).__name__


class _ItemCollectionRef(Laid, CollectionRef):
    """A container reached by ``ref[key]``, its children optionally from one default spec. Abstract.

    ``ref[key]`` is the child at ``key``: built from ``item`` when the
    container has one, else a bare ``ItemRef`` whose kind ``.to`` names at
    the use site. ``item`` is a Section class, a ref class or a
    ``Kind.slot(**props)`` spec. It rides the payload as a spec, as
    ``section_cls`` does, so it survives a tree rewrite. No class is made
    for it.

    Which keys a kind takes is three class settings: ``_positions`` (int
    keys), ``_names`` (str keys) and ``_parts``, the names the container
    places itself and answers by property (``card.actions``), refused as
    body keys so one place never holds two kinds.
    """

    _takes_item: ClassVar[bool] = True

    def __init__(
        self,
        address: object,
        *,
        item: type[Section] | type[Ref] | Slot | None = None,
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
        self._payload["item"] = as_spec(type(self).__name__, item)

    @classmethod
    def slot(cls, item: type[Section] | type[Ref] | Slot | None = None, /, **props: object) -> Self:
        """Declare this container as a slot, its children drawn from ``item`` by default."""
        declared = super().slot(**props)
        if item is not None:
            declared.kwargs["item"] = as_spec(cls.__name__, item)  # type: ignore[attr-defined]
        return declared

    def __getitem__(self, key: object) -> ItemRef:
        return self._child(key)

    def _child(self, key: object) -> ItemRef:
        """The child at ``key``, after checking this container takes such a key."""
        owner = self._owner_name()
        check_key(owner, key, positions=self._positions, names=self._names, parts=self._parts)
        return self._wrap_item_ref(key)

    def _wrap_item_ref(self, address: object) -> ItemRef:
        """The child at ``address``: from the ``item`` spec, or bare. Core's descent hook."""
        return child_at(self, address, self._payload.get("item"))


class DictCollectionRef(_ItemCollectionRef):
    """A container that takes its children by position and by name. Abstract.

    ``ref[0]`` is a position, drawn in number order; ``ref["k"]`` a name,
    drawn in the order first written. Both mix in one container. The key is
    a term like any address, so a computed key works too.
    """


class ListCollectionRef(_ItemCollectionRef):
    """A container that takes its children by position. Abstract.

    ``ref[i]`` is the child at index ``i``, an int or an int term. The
    browser draws indexed children in index order.
    """

    _names: ClassVar[bool] = False


class ShapeCollectionRef(Laid, CollectionRef):
    """A container whose children are its own named parts. Abstract.

    It takes no item template and cannot be subscripted: each part is a
    property (``field.control``).
    """
