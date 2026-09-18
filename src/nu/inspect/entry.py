"""Entries: what a declared class holds, and the record behind one of them.

Shared machinery for the two declarative kinds. A Shape declares slots, a
Service declares methods; both are class-level declarations that are never
instantiated, and both are read the same way - a flat list of named members,
each pointing at something that already has a record. "Entry" is that shared
word, and it is what lets one dispatch function serve both kinds.

Two levels, never a tree. ``entries_of`` gives the names and what each one
is; ``parse_entry`` resolves exactly one of them and hands back the record
the pointed-at thing already has - a RefRecord for a Ref slot or a Service
method, a ShapeRecord for a nested Shape. Nothing expands eagerly, because a
Shape can nest arbitrarily deep and an agent reading a 10-slot Shape wants 10
lines, then one lookup for the slot it cares about. The descent is the
reader's to drive.

A Service method resolves to a RefRecord rather than to an interaction
record: what a Service declares is a MethodRef subclass, and the interaction
it builds when called is named in that Ref's own Yields.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Any


if TYPE_CHECKING:
    from nu.domains.shape.dsl import Slot
    from nu.inspect.record import Record
    from nu.lang.typeinfo import TypeInfo


__all__ = [
    "Entry",
    "entries_of",
    "entry_names",
    "is_service",
    "is_shape",
    "nested_shape",
    "parse_entry",
]


@dataclass(frozen=True)
class Entry:
    """One named member of a declared class, and where to look next.

    ``kind`` is what the entry points at - ``ref``, ``shape`` or ``method`` -
    which is the only thing a reader needs to predict what a lookup will
    return. ``type`` is the declared type as written, rendered back from the
    annotation (``ShapesDictRef[int, Order]``). ``config`` is the declaration
    kwargs that the type does not already carry: the endpoint path on a
    Service method, a non-default view class on a slot.

    ``path`` is the dotted path that resolves this entry, so a reader can
    copy it straight into the next lookup.
    """

    name: str
    kind: str = ""
    type: str = ""
    config: str = ""
    path: str = ""


def is_shape(cls: object) -> bool:
    """True for a Shape subclass, the base itself excluded.

    The two DSLs are imported inside the function rather than at module
    scope: nu.inspect is imported early in ``nu/__init__``, before the
    domains, and a kind that describes user classes must not be what decides
    the import order of the package it lives in.
    """
    from nu.domains.shape.dsl import Shape
    from nu.lang.kinds import Ref

    return (
        isinstance(cls, type)
        and cls is not Shape
        and hasattr(cls, "_slots")
        and not issubclass(cls, Ref)
    )


def is_service(cls: object) -> bool:
    """True for a Service subclass, the base itself excluded."""
    from nu.domains.service.dsl import Service

    return isinstance(cls, type) and cls is not Service and hasattr(cls, "_methods")


def entry_names(cls: object) -> tuple[str, ...]:
    """The entry names ``cls`` declares. Empty for anything that declares none."""
    if is_service(cls):
        return tuple(cls._methods)  # type: ignore[attr-defined]
    return tuple(_declarations(cls))  # type: ignore[arg-type]


def entries_of(cls: type, path: str) -> tuple[Entry, ...]:
    """One Entry per member ``cls`` declares.

    ``path`` is where ``cls`` itself was reached, so each entry's path is
    reachable from what the reader already typed.

    Order is the order the metaclass collected the declarations in, which is
    source order only when a class declares them all one way; a Shape that
    mixes explicit ``.slot()`` assignments with bare annotations collects the
    assignments first. Reordering here would be inventing an order, so it is
    passed through as found.
    """
    if is_service(cls):
        return tuple(
            Entry(
                name=name,
                kind="method",
                type=method.ref_cls.__name__,
                config=_config(method.kwargs),
                path=f"{path}.{name}",
            )
            for name, method in cls._methods.items()  # type: ignore[attr-defined]
        )
    return tuple(_slot_entry(name, slot, path) for name, slot in _declarations(cls).items())


def parse_entry(cls: type, name: str, path: str = "") -> Record | None:
    """The record for one entry of ``cls``, or None when it declares no such name.

    Dispatches to whichever kind already covers the pointed-at thing rather
    than inventing an entry record: this is a lookup step, not a kind.
    """
    from nu.inspect.ref import parse_ref
    from nu.inspect.shape import parse_shape

    base = path or f"{cls.__module__}.{cls.__name__}.{name}"
    slot = _declarations(cls).get(name)
    if slot is not None:
        shape = nested_shape(cls, name)
        if shape is not None:
            return parse_shape(shape, path=base)
        return parse_ref(slot.ref_cls, path=base)
    method = getattr(cls, "_methods", {}).get(name) if is_service(cls) else None
    if method is not None:
        return parse_ref(method.ref_cls, path=base)
    return None


def nested_shape(cls: type, name: str) -> type | None:
    """The Shape a slot navigates into, or None when the slot is a leaf.

    A nested slot is written three ways - ``rel: Order = ShapeRef.slot(Order)``,
    ``rel: ShapeRef[Order]``, or a bare ``rel = ShapeRef.slot(Order)`` with no
    annotation at all - and the last one resolves no type info, so the ref
    class plus its ``shape_type`` kwarg is the reading that covers all three.
    A collection of shapes (``ShapesDictRef[int, Order]``) is not nested: the
    entry is the collection, and its record is the collection's.
    """
    slot = _declarations(cls).get(name)
    return _held_shape(slot) if slot is not None else None


# --- reading a slot -------------------------------------------------------


def _slot_entry(name: str, slot: Slot, path: str) -> Entry:
    shape = _held_shape(slot)
    shown = (
        shape.__name__ if shape is not None else _type_text(slot._resolve_type_info(), slot.ref_cls)
    )
    return Entry(
        name=name,
        kind="shape" if shape is not None else "ref",
        type=shown,
        config=_config({**slot.kwargs, **slot.props}, skip_types_in=shown),
        path=f"{path}.{name}",
    )


def _held_shape(slot: Slot) -> type | None:
    info = slot._resolve_type_info()
    if info is not None and info.is_shape:
        return info.py_type  # type: ignore[no-any-return]
    if not _navigates_shape(slot.ref_cls):
        return None
    held = slot.kwargs.get("shape_type")
    return held if is_shape(held) else None  # type: ignore[return-value]


def _navigates_shape(ref_cls: type) -> bool:
    """True for the ref family that descends into one nested Shape."""
    from nu.domains.shape.refs.shape import ShapeRef

    return isinstance(ref_cls, type) and issubclass(ref_cls, ShapeRef)


def _type_text(info: TypeInfo | None, ref_cls: type) -> str:
    """The declared type as written. Falls back to the ref class.

    ``_resolve_type_info`` fails soft on an unresolved forward ref and on a
    slot declared with no annotation at all, so absent type info is normal
    rather than exceptional; the ref class is then the whole truth.
    """
    if info is None:
        return ref_cls.__name__
    return _render_type(info)


def _render_type(info: TypeInfo) -> str:
    name = getattr(info.py_type, "__name__", None) or ("Any" if info.is_any else str(info.py_type))
    args = [child for child in (info.key, info.elem) if child is not None]
    if not args:
        return name
    return f"{name}[{', '.join(_render_type(child) for child in args)}]"


def _config(kwargs: dict[str, Any], skip_types_in: str = "") -> str:
    """The declaration kwargs the rendered type does not already carry."""
    parts: list[str] = []
    for key, value in kwargs.items():
        if value is None or value == {} or value == () or value == []:
            continue
        if isinstance(value, type) and value.__name__ in skip_types_in:
            continue
        parts.append(f"{key}={_value_text(value)}")
    return ", ".join(parts)


def _value_text(value: object) -> str:
    if isinstance(value, type):
        return value.__name__
    return repr(value)


# --- markers ---------------------------------------------------------------


def _declarations(cls: type) -> dict[str, Slot]:
    return getattr(cls, "_slots", {}) if is_shape(cls) else {}
