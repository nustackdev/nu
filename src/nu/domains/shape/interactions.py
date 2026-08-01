"""Shape fabric queries and commands — all shape interactions in one place.

Read queries (polymorphic on Ref class):
- ``LoadQuery``          - yield the value at the slot-0 Ref (EMPTY if absent).
- ``ExistsQuery``        - True if the slot-0 Ref's address is bound.
- ``MissingQuery``       - True if the slot-0 Ref's address is unbound.
- ``ExtractQuery``       - materialise the full subtree rooted at the Ref.
- ``AdvanceCursorQuery`` - read the next key after the cursor on an ordered view.

Write commands (polymorphic on Ref class):
- ``SetCommand`` - write the slot-1 value to the slot-0 Ref's address.
- ``EraseCommand``  - remove the slot-0 Ref from its fabric.

The Item/Collection split is dropped; the substrate optimizer matches on
the concrete Ref class. ``*Cmd`` suffix dropped by naming convention.

Reactive queries (``OnChangeQuery``, ``OnChildChangeQuery``,
``OnChildrenChangeQuery``, ``OnDescendantsChangeQuery``,
``OnPrimitiveChangeQuery``) live in ``nu.core.reactive`` -- one unified
interface for all substrates, reached through the shape Form mixins.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from nu.engine.structure import Declared
from nu.lang import Command, ScalarQuery
from nu.lang.sentinels import EMPTY, INVALID


if TYPE_CHECKING:
    from collections.abc import Callable

    from nu.lang.runtime import Runtime

__all__ = [
    "AdvanceCursorQuery",
    "EraseCommand",
    "ExistsQuery",
    "ExtractQuery",
    "LoadQuery",
    "MissingQuery",
    "PrimitiveSetCommand",
    "SetCommand",
]


# ---------------------------------------------------------------------------
# Read queries
# ---------------------------------------------------------------------------


class LoadQuery(ScalarQuery):
    """Yield the value at the slot-0 Ref; EMPTY if the address is unbound."""

    def _compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        ref_thunk = children[0]

        def thunk(rt: Runtime) -> object:
            return ref_thunk(rt)

        return thunk

    def _acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        ref_thunk = children[0]

        async def athunk(rt: Runtime) -> object:
            return await ref_thunk(rt)

        return athunk


class ExistsQuery(ScalarQuery):
    """Yield True if the slot-0 Ref's address is bound (value is not a sentinel)."""

    def _compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        ref_thunk = children[0]

        def thunk(rt: Runtime) -> bool:
            v = ref_thunk(rt)
            return v is not EMPTY and v is not INVALID

        return thunk

    def _acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        ref_thunk = children[0]

        async def athunk(rt: Runtime) -> bool:
            v = await ref_thunk(rt)
            return v is not EMPTY and v is not INVALID

        return athunk


class MissingQuery(ScalarQuery):
    """Yield True if the slot-0 Ref's address is unbound (value is a sentinel)."""

    def _compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        ref_thunk = children[0]

        def thunk(rt: Runtime) -> bool:
            v = ref_thunk(rt)
            return v is EMPTY or v is INVALID

        return thunk

    def _acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
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
    is unwrapped when present, matching ``CollectionExtract`` mechanics.
    """

    def _compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        ref_thunk = children[0]

        def thunk(rt: Runtime) -> object:
            view = ref_thunk(rt)
            if view is EMPTY or view is INVALID:
                return view  # preserve EMPTY vs INVALID identity
            if hasattr(view, "eager"):
                view = view.eager
            return view.extract()

        return thunk

    def _acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        ref_thunk = children[0]

        async def athunk(rt: Runtime) -> object:
            view = await ref_thunk(rt)
            if view is EMPTY or view is INVALID:
                return view  # preserve EMPTY vs INVALID identity
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

    def _compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        source_thunk, cursor_thunk = children[0], children[1]

        def thunk(rt: Runtime) -> object:
            view = source_thunk(rt)
            cursor = cursor_thunk(rt)
            if cursor is EMPTY or cursor is INVALID:
                cursor = None
            return view.next_key_after(cursor)

        return thunk

    def _acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
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


class SetCommand(Command):
    """Write the slot-1 value to the slot-0 structured Ref's address."""

    _mutates = Declared(value=frozenset({0}), name="mutates")

    def _compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        ref = self._children[0]
        value = children[1]

        def thunk(rt: Runtime) -> None:
            v = value(rt)
            if v is EMPTY or v is INVALID:
                raise ValueError("cannot store sentinel value")
            ref._write(rt, v, rt.program.children[nid][0])

        return thunk

    def _acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        ref = self._children[0]
        value = children[1]

        async def athunk(rt: Runtime) -> None:
            v = await value(rt)
            if v is EMPTY or v is INVALID:
                raise ValueError("cannot store sentinel value")
            await ref._awrite(rt, v, rt.program.children[nid][0])

        return athunk


class EraseCommand(Command):
    """Remove the slot-0 structured Ref from its fabric."""

    _mutates = Declared(value=frozenset({0}), name="mutates")

    def _compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        ref = self._children[0]

        def thunk(rt: Runtime) -> None:
            ref._erase(rt, rt.program.children[nid][0])

        return thunk

    def _acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        ref = self._children[0]

        async def athunk(rt: Runtime) -> None:
            await ref._aerase(rt, rt.program.children[nid][0])

        return athunk


class PrimitiveSetCommand(Command):
    """Write the slot-1 value to the slot-0 Ref via ``_primitive_write``.

    Bypasses the compound-value decomposition of ``SetCommand`` (which
    recurses into containers).  Use for Refs that store compound values as a
    single opaque blob (e.g. ``PrimitiveDictRef``, ``PrimitiveListRef``,
    ``PrimitiveSetRef`` substrates).

    Raises ``ValueError`` when the value slot evaluates to a sentinel,
    matching ``ItemPrimitiveSetCmd`` mechanics.

    Requires the parent view to support ``_primitive_write`` /
    ``_aprimitive_write`` (the abstract hook declared on ``StructuredRef``).
    """

    _mutates = Declared(value=frozenset({0}), name="mutates")

    def _compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        ref = self._children[0]
        value = children[1]

        def thunk(rt: Runtime) -> None:
            v = value(rt)
            if v is EMPTY or v is INVALID:
                raise ValueError("cannot store sentinel value")
            ref._primitive_write(rt, v, rt.program.children[nid][0])  # type: ignore[attr-defined]

        return thunk

    def _acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        ref = self._children[0]
        value = children[1]

        async def athunk(rt: Runtime) -> None:
            v = await value(rt)
            if v is EMPTY or v is INVALID:
                raise ValueError("cannot store sentinel value")
            await ref._aprimitive_write(rt, v, rt.program.children[nid][0])  # type: ignore[attr-defined]

        return athunk
