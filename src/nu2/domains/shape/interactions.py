"""Shape fabric queries and commands — all shape interactions in one place.

Read queries (polymorphic on Ref class):
- ``LoadQuery``          - yield the value at the slot-0 Ref (EMPTY if absent).
- ``ExistsQuery``        - True if the slot-0 Ref's address is bound.
- ``MissingQuery``       - True if the slot-0 Ref's address is unbound.
- ``ExtractQuery``       - materialise the full subtree rooted at the Ref.
- ``AdvanceCursorQuery`` - read the next key after the cursor on an ordered view.

Reactive observation queries (shape-domain; require structured Refs with tree structure):
- ``OnChildChangeQuery``        subscribe to changes on one specific child.
- ``OnChildrenChangeQuery``     subscribe to changes on any immediate child.
- ``OnDescendantsChangeQuery``  subscribe to descendants matching a pattern.

(The generic ``OnChangeQuery`` — subscribe to any change on self — lives in
``nu2.forms.reactive`` because it works on any observable Ref, not just shapes.)

Write commands (polymorphic on Ref class):
- ``StoreCommand`` - write the slot-1 value to the slot-0 Ref's address.
- ``EraseCommand``  - remove the slot-0 Ref from its fabric.

The Item/Collection split from v1 is dropped; the substrate optimizer matches on
the concrete Ref class. ``*Cmd`` suffix dropped per v2 naming convention.

v1 reference: ``src/nu/shapes/queries/item.py``,
              ``src/nu/shapes/queries/collection.py``,
              ``src/nu/shapes/queries/reactive.py``,
              ``src/nu/shapes/commands/item.py``,
              ``src/nu/shapes/commands/collection.py``.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from nu2.engine.structure import Declared
from nu2.lang import Command, ScalarQuery
from nu2.lang.sentinels import EMPTY, INVALID


if TYPE_CHECKING:
    from collections.abc import Callable

    from nu2.lang.runtime import Runtime

__all__ = [
    "AdvanceCursorQuery",
    "EraseCommand",
    "ExistsQuery",
    "ExtractQuery",
    "LoadQuery",
    "MissingQuery",
    "OnChildChangeQuery",
    "OnChildrenChangeQuery",
    "OnDescendantsChangeQuery",
    "PrimitiveStoreCommand",
    "StoreCommand",
]


# ---------------------------------------------------------------------------
# Read queries
# ---------------------------------------------------------------------------


class LoadQuery(ScalarQuery):
    """Yield the value at the slot-0 Ref; EMPTY if the address is unbound."""

    def compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:  # noqa: D102
        ref_thunk = children[0]

        def thunk(rt: Runtime) -> object:
            return ref_thunk(rt)

        return thunk

    def acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:  # noqa: D102
        ref_thunk = children[0]

        async def athunk(rt: Runtime) -> object:
            return await ref_thunk(rt)

        return athunk


class ExistsQuery(ScalarQuery):
    """Yield True if the slot-0 Ref's address is bound (value is not a sentinel)."""

    def compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:  # noqa: D102
        ref_thunk = children[0]

        def thunk(rt: Runtime) -> bool:
            v = ref_thunk(rt)
            return v is not EMPTY and v is not INVALID

        return thunk

    def acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:  # noqa: D102
        ref_thunk = children[0]

        async def athunk(rt: Runtime) -> bool:
            v = await ref_thunk(rt)
            return v is not EMPTY and v is not INVALID

        return athunk


class MissingQuery(ScalarQuery):
    """Yield True if the slot-0 Ref's address is unbound (value is a sentinel)."""

    def compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:  # noqa: D102
        ref_thunk = children[0]

        def thunk(rt: Runtime) -> bool:
            v = ref_thunk(rt)
            return v is EMPTY or v is INVALID

        return thunk

    def acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:  # noqa: D102
        ref_thunk = children[0]

        async def athunk(rt: Runtime) -> bool:
            v = await ref_thunk(rt)
            return v is EMPTY or v is INVALID

        return athunk


class ExtractQuery(ScalarQuery):
    """Materialise the full subtree at the slot-0 Ref via ``view.extract()``.

    Distinct from ``LoadQuery``: LoadQuery yields the value at the Ref's
    address; ExtractQuery recursively materialises the subtree into a plain
    Python value (dict / list / nested mix). The view may be lazy; ``.eager``
    is unwrapped when present, matching v1 ``CollectionExtract`` mechanics.
    """

    def compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:  # noqa: D102
        ref_thunk = children[0]

        def thunk(rt: Runtime) -> object:
            view = ref_thunk(rt)
            if view is EMPTY or view is INVALID:
                return view  # preserve EMPTY vs INVALID identity (v1 parity)
            if hasattr(view, "eager"):
                view = view.eager
            return view.extract()

        return thunk

    def acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:  # noqa: D102
        ref_thunk = children[0]

        async def athunk(rt: Runtime) -> object:
            view = await ref_thunk(rt)
            if view is EMPTY or view is INVALID:
                return view  # preserve EMPTY vs INVALID identity (v1 parity)
            if hasattr(view, "eager"):
                view = view.eager
            return view.extract()

        return athunk


class AdvanceCursorQuery(ScalarQuery):
    """Read the next key after the cursor on an ordered view.

    Children: ``[source_ref, cursor_ref]``. Calls ``view.next_key_after(cursor)``
    on the ordered view yielded by slot 0. A ``None`` or absent cursor starts
    from the beginning. Returns ``(log_key, actual_key)`` or ``None`` if exhausted.
    """

    def compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:  # noqa: D102
        source_thunk, cursor_thunk = children[0], children[1]

        def thunk(rt: Runtime) -> object:
            view = source_thunk(rt)
            cursor = cursor_thunk(rt)
            if cursor is EMPTY or cursor is INVALID:
                cursor = None
            return view.next_key_after(cursor)

        return thunk

    def acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:  # noqa: D102
        source_thunk, cursor_thunk = children[0], children[1]

        async def athunk(rt: Runtime) -> object:
            view = await source_thunk(rt)
            cursor = await cursor_thunk(rt)
            if cursor is EMPTY or cursor is INVALID:
                cursor = None
            return view.next_key_after(cursor)

        return athunk


# ---------------------------------------------------------------------------
# Write commands
# ---------------------------------------------------------------------------


class StoreCommand(Command):
    """Write the slot-1 value to the slot-0 structured Ref's address."""

    mutates = Declared(value=frozenset({0}))

    def compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:  # noqa: D102
        ref = self.children[0]
        value = children[1]

        def thunk(rt: Runtime) -> None:
            v = value(rt)
            if v is EMPTY or v is INVALID:
                raise ValueError("cannot store sentinel value")
            ref.write(rt, v, rt.program.children[nid][0])

        return thunk

    def acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:  # noqa: D102
        ref = self.children[0]
        value = children[1]

        async def athunk(rt: Runtime) -> None:
            v = await value(rt)
            if v is EMPTY or v is INVALID:
                raise ValueError("cannot store sentinel value")
            await ref.awrite(rt, v, rt.program.children[nid][0])

        return athunk


class EraseCommand(Command):
    """Remove the slot-0 structured Ref from its fabric."""

    mutates = Declared(value=frozenset({0}))

    def compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:  # noqa: D102
        ref = self.children[0]

        def thunk(rt: Runtime) -> None:
            ref.erase(rt, rt.program.children[nid][0])

        return thunk

    def acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:  # noqa: D102
        ref = self.children[0]

        async def athunk(rt: Runtime) -> None:
            await ref.aerase(rt, rt.program.children[nid][0])

        return athunk


class PrimitiveStoreCommand(Command):
    """Write the slot-1 value to the slot-0 Ref via ``_primitive_write``.

    Bypasses the compound-value decomposition of ``StoreCommand`` (which
    recurses into containers).  Use for Refs that store compound values as a
    single opaque blob (e.g. ``PrimitiveDictRef``, ``PrimitiveListRef``,
    ``PrimitiveSetRef`` substrates).

    Raises ``ValueError`` when the value slot evaluates to a sentinel —
    matching v1 ``ItemPrimitiveStoreCmd`` mechanics.

    Requires the parent view to support ``_primitive_write`` /
    ``_aprimitive_write`` (the abstract hook declared on ``_StructuredRef``).

    v1 reference: ``src/nu/shapes/commands/item.py::ItemPrimitiveStoreCmd``.
    """

    mutates = Declared(value=frozenset({0}))

    def compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:  # noqa: D102
        ref = self.children[0]
        value = children[1]

        def thunk(rt: Runtime) -> None:
            v = value(rt)
            if v is EMPTY or v is INVALID:
                raise ValueError("cannot store sentinel value")
            ref._primitive_write(rt, v, rt.program.children[nid][0])  # type: ignore[attr-defined]

        return thunk

    def acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:  # noqa: D102
        ref = self.children[0]
        value = children[1]

        async def athunk(rt: Runtime) -> None:
            v = await value(rt)
            if v is EMPTY or v is INVALID:
                raise ValueError("cannot store sentinel value")
            await ref._aprimitive_write(rt, v, rt.program.children[nid][0])  # type: ignore[attr-defined]

        return athunk


# ---------------------------------------------------------------------------
# Reactive observation queries (shape-domain)
# ---------------------------------------------------------------------------


class OnChildChangeQuery(ScalarQuery):
    """Subscribe to changes on the slot-1 address within the slot-0 Ref's view.

    Shape-domain: requires a structured Ref whose view exposes
    ``on_child_change(address)``.

    v1 reference: ``src/nu/shapes/queries/reactive.py::OnChildChange``.
    """

    def compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:  # noqa: D102
        view_thunk, address_thunk = children[0], children[1]

        def thunk(rt: Runtime) -> object:
            view = view_thunk(rt)
            if view is EMPTY or view is INVALID:
                return INVALID
            address = address_thunk(rt)
            if address is EMPTY or address is INVALID:
                return INVALID
            return view.on_child_change(address)

        return thunk

    def acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:  # noqa: D102
        view_thunk, address_thunk = children[0], children[1]

        async def athunk(rt: Runtime) -> object:
            view = await view_thunk(rt)
            if view is EMPTY or view is INVALID:
                return INVALID
            address = await address_thunk(rt)
            if address is EMPTY or address is INVALID:
                return INVALID
            return view.on_child_change(address)

        return athunk


class OnChildrenChangeQuery(ScalarQuery):
    """Subscribe to changes on all immediate children of the slot-0 Ref's view.

    Shape-domain: requires a structured Ref whose view exposes
    ``on_children_change()``.

    v1 reference: ``src/nu/shapes/queries/reactive.py::OnChildrenChange``.
    """

    def compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:  # noqa: D102
        view_thunk = children[0]

        def thunk(rt: Runtime) -> object:
            view = view_thunk(rt)
            if view is EMPTY or view is INVALID:
                return INVALID
            return view.on_children_change()

        return thunk

    def acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:  # noqa: D102
        view_thunk = children[0]

        async def athunk(rt: Runtime) -> object:
            view = await view_thunk(rt)
            if view is EMPTY or view is INVALID:
                return INVALID
            return view.on_children_change()

        return athunk


class OnDescendantsChangeQuery(ScalarQuery):
    """Subscribe to descendants matching a pattern on the slot-0 Ref's view.

    Shape-domain: requires a structured Ref whose view exposes
    ``on_descendants_change(p0, p1, ...)``.

    Children: ``[ref, pattern_0, pattern_1, ...]``. At least one pattern child
    is required. Calls ``view.on_descendants_change(p0, p1, ...)``.

    v1 reference: ``src/nu/shapes/queries/reactive.py::OnDescendantsChange``
    (the v1 substrate API misspelled this as ``on_descendents_change``; v2
    substrates implement the correct spelling).
    """

    def compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:  # noqa: D102
        view_thunk = children[0]
        pattern_thunks = children[1:]

        def thunk(rt: Runtime) -> object:
            view = view_thunk(rt)
            if view is EMPTY or view is INVALID:
                return INVALID
            if not pattern_thunks:
                raise ValueError("Pattern cannot be empty for on_descendants_change")
            pattern = []
            for pt in pattern_thunks:
                p = pt(rt)
                if p is EMPTY or p is INVALID:
                    return INVALID
                pattern.append(p)
            return view.on_descendants_change(pattern[0], *pattern[1:])

        return thunk

    def acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:  # noqa: D102
        view_thunk = children[0]
        pattern_thunks = children[1:]

        async def athunk(rt: Runtime) -> object:
            view = await view_thunk(rt)
            if view is EMPTY or view is INVALID:
                return INVALID
            if not pattern_thunks:
                raise ValueError("Pattern cannot be empty for on_descendants_change")
            pattern = []
            for pt in pattern_thunks:
                p = await pt(rt)
                if p is EMPTY or p is INVALID:
                    return INVALID
                pattern.append(p)
            return view.on_descendants_change(pattern[0], *pattern[1:])

        return athunk
