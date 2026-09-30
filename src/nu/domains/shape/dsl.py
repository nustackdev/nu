"""Declaring shapes: a Shape class names its slots, and each slot builds a ref.

``Slot`` is the factory, ``ShapeMeta`` collects slots at class-definition time,
and ``SlotDescriptor`` hands out a fresh ref on every class access. A slot may
also declare what its ref holds; that declaration rides on the ref's payload as
``type_info``, and it is the one place a ref's declared types live. Slot props
land on ``_payload["props"]`` the same way, so a ref can see what its slot
declared.

A slot is written two ways, and both give the same ref with the same typing:

- **Explicit**: ``orders = kv.DictRef.slot(Order, key=int)``. The ref class's
  ``slot`` builds the ``Slot`` and its declaration.
- **Annotation**: ``orders: kv.DictRef[int, Order]``. The metaclass reads the
  annotation, synthesizes the ``Slot`` and declares the same ``TypeInfo`` from
  it. A bare ref class (``name: kv.StrRef``) synthesizes a plain ``Slot``.

A bare Shape annotation (``rel: Order``) cannot name the fabric, so it needs an
explicit ``= <fabric>.ShapeRef.slot(Order)``; alone it is an error. Any other
annotation synthesizes nothing and only declares the type, next to an explicit
slot. When both spellings are written, the explicit declaration wins.

Example::

    class Profile(nu.Shape):
        name: nm.StrRef
        tags: nm.ListRef[str]
        orders: nm.DictRef[int, Order]
        rel: Order = nm.ShapeRef.slot(Order)
        events = nv.Kh57Ref.slot(int, view=nv.Kh57View)
"""

from __future__ import annotations

import typing
from abc import ABCMeta
from typing import TYPE_CHECKING, ClassVar, Generic, TypeVar

from nu.lang import Ref
from nu.lang.typeinfo import TypeInfo


if TYPE_CHECKING:
    from nu.domains.shape.base import StructuredRef

__all__ = [
    "Shape",
    "ShapeMeta",
    "Slot",
    "SlotDescriptor",
]

_RefT = TypeVar("_RefT")


class Slot(Generic[_RefT]):
    """Factory carrying a Ref class and kwargs; create_ref produces the Ref."""

    def __init__(
        self,
        ref_cls: type[_RefT],
        props: dict[str, object] | None = None,
        type_info: TypeInfo | None = None,
        **kwargs: object,
    ) -> None:
        self.name: str | None = None
        self.ref_cls = ref_cls
        self.kwargs = kwargs
        self.props: dict[str, object] = props or {}
        self._owner_cls: type | None = None
        self._type_info = type_info

    def create_ref(
        self,
        owner_shape: type[Shape],
        parent_ref: StructuredRef | None = None,
    ) -> _RefT:
        """Instantiate the Ref, wiring owner_shape and parent_ref."""
        ref = self.ref_cls(  # type: ignore[call-arg]
            self.name,
            owner_shape=owner_shape,
            parent_ref=parent_ref,
            **self.kwargs,
        )
        ti = self._resolve_type_info()
        if ti is not None:
            ref._payload["type_info"] = ti
        if self.props:
            # Payload, not an attribute: ``Term._with_children`` carries it
            # across a tree rewrite, so the props a slot declared survive
            # re-rooting and stay reachable from the ref itself.
            ref._payload["props"] = dict(self.props)
        return ref

    def _resolve_type_info(self) -> TypeInfo | None:
        """What the slot declares its ref holds: explicit, else read off the annotation.

        The annotation is resolved lazily and memoized. Fails soft: if forward
        refs in the annotations can't be resolved yet, returns ``None`` this
        time and retries on next access.
        """
        if self._type_info is not None:
            return self._type_info
        if self._owner_cls is None or self.name is None:
            return None
        try:
            hints = typing.get_type_hints(self._owner_cls)
        except NameError:
            return None
        ann = hints.get(self.name)
        if ann is None:
            return None
        self._type_info = TypeInfo.from_annotation(ann)
        return self._type_info

    def __repr__(self) -> str:
        return f"<Slot name={self.name!r} ref_cls={self.ref_cls.__name__}>"


class SlotDescriptor:
    """Descriptor that returns a Ref when a slot name is accessed on a Shape class."""

    def __init__(self, name: str, slot: Slot) -> None:
        self.name = name
        self.slot = slot

    def __get__(self, obj: object, objtype: type[Shape] | None = None) -> StructuredRef:
        """Return a Ref rooted at objtype for this slot."""
        if objtype is None:
            raise TypeError("SlotDescriptor requires a Shape class")
        return self.slot.create_ref(owner_shape=objtype, parent_ref=None)  # type: ignore[return-value]

    def __set__(self, obj: object, value: object) -> None:
        """Slots are read-only structure definitions."""
        raise AttributeError(
            f"Cannot set slot '{self.name}': slots are read-only structure definitions"
        )


class ShapeMeta(ABCMeta):
    """Metaclass that collects Slot definitions and replaces them with SlotDescriptors."""

    def __new__(
        mcs,
        name: str,
        bases: tuple[type, ...],
        namespace: dict[str, object],
        **kwargs: object,
    ) -> type:
        """Build the Shape class, collecting explicit + annotation-synthesized Slots."""
        slots: dict[str, Slot] = {}
        for base in bases:
            if hasattr(base, "_slots"):
                slots.update(base._slots)

        for field_name, value in list(namespace.items()):
            if isinstance(value, Slot):
                value.name = field_name
                slots[field_name] = value

        namespace["_slots"] = slots
        cls = super().__new__(mcs, name, bases, namespace)

        own_annotations = namespace.get("__annotations__", {})
        if own_annotations:
            try:
                hints = typing.get_type_hints(cls)
            except NameError:
                hints = {}
            for field_name in own_annotations:
                if field_name in slots or field_name.startswith("_"):
                    continue
                ann = hints.get(field_name)
                if ann is None:
                    continue
                synth = _synthesize_slot(ann, cls, field_name)
                if synth is not None:
                    synth.name = field_name
                    synth._owner_cls = cls
                    slots[field_name] = synth

        for value in namespace.values():
            if isinstance(value, Slot) and value._owner_cls is None:
                value._owner_cls = cls

        inherited = {n for base in bases for n in getattr(base, "_slots", {})}
        _check_slot_names(name, {n: s for n, s in slots.items() if n not in inherited})

        for field_name, slot in slots.items():
            setattr(cls, field_name, SlotDescriptor(field_name, slot))
        return cls


def _public_names(cls: type) -> set[str]:
    """Every public attribute ``cls`` carries, methods and properties alike."""
    return {n for n in dir(cls) if not n.startswith("_")}


def _shape_ref_classes() -> list[type]:
    """Every ShapeRef class defined so far: the nu blueprint and each fabric's."""
    from nu.domains.shape.shape import ShapeRef

    found: list[type] = []
    todo: list[type] = [ShapeRef]
    while todo:
        ref_cls = todo.pop()
        if ref_cls not in found:
            found.append(ref_cls)
            todo.extend(ref_cls.__subclasses__())
    return found


def _check_slot_names(shape: str, slots: dict[str, Slot]) -> None:
    """Refuse a slot named after a method or attribute of a ref.

    A slot is reached as an attribute of the shape ref above it
    (``User.profile.email``), and that lookup goes through the ref's own
    attributes first: a slot named ``len`` or ``iter`` would silently reach the
    ref method instead. The reserved names are read off every ShapeRef class
    defined so far, the nu blueprint and each fabric's (the class a nested
    shape slot produces), so they follow the surface as it grows.
    """
    shape_refs = _shape_ref_classes()
    for field_name in slots:
        for ref_cls in shape_refs:
            if field_name in _public_names(ref_cls):
                msg = (
                    f"Shape {shape}: slot {field_name!r} clashes with "
                    f"{ref_cls.__qualname__}.{field_name}. A slot is reached as an "
                    f"attribute of its ref, so `ref.{field_name}` would reach the "
                    f"ref's own {field_name!r}, not the slot. Rename the slot "
                    f"(e.g. {field_name + '_'!r})"
                )
                raise TypeError(msg)


def _synthesize_slot(ann: object, cls: type, field_name: str) -> Slot | None:
    """Synthesize a ``Slot`` from a Shape-slot annotation, if the shape allows.

    A ref class, bare or parametric, becomes a ``Slot`` of that class; its type
    arguments are the slot's declaration, read back through the annotation. A
    ref whose constructor needs one of them (``ShapeRef[Order]``) takes it from
    its ``_slot_kwargs_from_type_args``. Returns ``None`` when the annotation
    does not name a ref. Raises ``TypeError`` for a bare Shape annotation, since
    it cannot name the fabric.
    """
    origin = typing.get_origin(ann)

    if origin is not None and isinstance(origin, type) and issubclass(origin, Ref):
        deriver = getattr(origin, "_slot_kwargs_from_type_args", None)
        kwargs = deriver(typing.get_args(ann)) if deriver is not None else {}
        return Slot(origin, **kwargs)

    if isinstance(ann, type) and issubclass(ann, Ref):
        return Slot(ann)

    if isinstance(ann, type) and hasattr(ann, "_slots") and not issubclass(ann, Ref):
        msg = (
            f"Bare Shape annotation {cls.__name__}.{field_name}: "
            f"{ann.__name__!r} requires an explicit `.slot()` naming the "
            f"fabric, e.g. `= nm.ShapeRef.slot({ann.__name__})`."
        )
        raise TypeError(msg)

    return None


class Shape(metaclass=ShapeMeta):
    """Declarative structure definition using Slots. Never instantiated.

    Slots are replaced by SlotDescriptors at class-definition time.
    All access is at class level; Shape instances are never created.

    Example::

        class Profile(Shape):
            name: nm.StrRef
            age:  nm.IntRef

        class User(Shape):
            name: nm.StrRef
            profile: Profile = nm.ShapeRef.slot(Profile)

        User.name            # -> Ref
        User.profile.email   # -> Ref (nested via ShapeRef.__getattr__)
    """

    _slots: ClassVar[dict[str, Slot]] = {}
