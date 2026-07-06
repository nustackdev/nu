"""Shape DSL: Shape, Slot, ShapeMeta, SlotDescriptor.

Metaclass-driven DSL for declaring hierarchical document structures.
Slot is the factory; ShapeMeta collects slots at class-definition time;
SlotDescriptor exposes them as Refs on class access.

Under the task-119 typing discipline, a Shape slot annotation IS the ref
class (parametric or bare). The metaclass reads the annotation, synthesizes
a ``Slot`` when none is assigned, and stamps a recursive ``TypeInfo`` onto
each created Ref's ``_payload["type_info"]``.

Recognised annotation forms:

- **Bare ref class** (``nm.StrRef``, ``nd.HeadingRef``) - synthesizes
  ``Slot(<ref_cls>)``. Explicit ``= <ref_cls>.slot()`` is optional.
- **Parametric ref class** (``nv.PrimitiveListRef[str]``,
  ``nm.ShapesDictRef[int, Order]``) - synthesizes
  ``Slot(<origin>, **kwargs)`` where kwargs come from the origin's
  ``_slot_kwargs_from_type_args`` classmethod.
- **Bare Shape subclass** (``Order``) - shorthand for a ``ShapeRef``
  navigating that shape. Requires an explicit ``= <fabric>.ShapeRef.slot(...)``
  because the annotation alone cannot name the fabric. Bare Shape without
  an assignment is a hard error.
- **Anything else** (primitives, native container generics, ``Any``, ...):
  no synthesis. Legacy ``= <Ref>.slot(T)`` continues to work; the
  annotation still stamps a ``TypeInfo`` on the payload.

Example::

    class Profile(nu.Shape):
        # bare ref classes (no config): annotation only
        name: nm.StrRef
        age:  nm.IntRef

        # parametric refs
        tags:   nv.PrimitiveListRef[str]
        orders: nm.ShapesDictRef[int, Order]

        # bare Shape + explicit ``.slot()`` for fabric
        rel: Order = nm.ShapeRef.slot(Order)

        # with config
        top10: nv.Kh57Ref[int] = nv.Kh57Ref.slot(sample_size=10)
"""

from __future__ import annotations

import typing
from abc import ABCMeta
from typing import TYPE_CHECKING, ClassVar, Generic, TypeVar

from nu.lang import Ref
from nu.lang.typeinfo import TypeInfo


if TYPE_CHECKING:
    from nu.domains.shape.refs.base import StructuredRef

__all__ = [
    "Shape",
    "ShapeMeta",
    "Slot",
    "SlotDescriptor",
]

_RefT = TypeVar("_RefT")


class Slot(Generic[_RefT]):  # noqa: UP046
    """Factory carrying a Ref class and kwargs; create_ref produces the Ref."""

    def __init__(self, ref_cls: type[_RefT], **kwargs: object) -> None:
        self.name: str | None = None
        self.ref_cls = ref_cls
        self.kwargs = kwargs
        self._owner_cls: type | None = None
        self._type_info_cache: TypeInfo | None = None

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
        return ref

    def _resolve_type_info(self) -> TypeInfo | None:
        """Lazily resolve the annotation-driven ``TypeInfo`` (memoized).

        Fails soft: if forward refs in the annotations can't be resolved
        yet, returns ``None`` this time and retries on next access.
        """
        if self._type_info_cache is not None:
            return self._type_info_cache
        if self._owner_cls is None or self.name is None:
            return None
        try:
            hints = typing.get_type_hints(self._owner_cls)
        except NameError:
            return None
        ann = hints.get(self.name)
        if ann is None:
            return None
        self._type_info_cache = TypeInfo.from_annotation(ann)
        return self._type_info_cache

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
            f"Cannot set slot '{self.name}' — slots are read-only structure definitions"
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

        for field_name, slot in slots.items():
            setattr(cls, field_name, SlotDescriptor(field_name, slot))
        return cls


def _synthesize_slot(ann: object, cls: type, field_name: str) -> Slot | None:
    """Synthesize a ``Slot`` from a Shape-slot annotation, if the shape allows.

    Returns ``None`` when the annotation does not correspond to a Ref (the
    field will fall back to any explicit assignment, or be treated as a
    non-slot). Raises ``TypeError`` for bare Shape annotations that lack an
    explicit ``.slot()`` (fabric cannot be inferred).
    """
    origin = typing.get_origin(ann)
    args = typing.get_args(ann)

    if origin is not None and isinstance(origin, type) and issubclass(origin, Ref):
        deriver = getattr(origin, "_slot_kwargs_from_type_args", None)
        if deriver is None:
            msg = (
                f"Cannot synthesize Slot for {cls.__name__}.{field_name}: "
                f"{origin.__name__} is a parametric Ref but does not define "
                f"_slot_kwargs_from_type_args."
            )
            raise TypeError(msg)
        return Slot(origin, **deriver(args))

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
