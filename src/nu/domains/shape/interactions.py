"""Shape fabric queries and commands: all shape interactions in one place.

Read queries (polymorphic on Ref class):
- ``Load``: yield the value at the slot-0 Ref (NULL if absent).
- ``Exists``: True if the slot-0 Ref's address holds a value.
- ``Extract``: materialise the full subtree rooted at the Ref.
- ``AdvanceCursor``: read the next key after the cursor on an ordered view.

Write commands (polymorphic on Ref class):
- ``SetCmd``: write the slot-1 value to the slot-0 Ref's address.
- ``Erase``: remove the slot-0 Ref from its fabric.

The substrate optimizer matches on the concrete Ref class.

Reactive queries (``OnChange``, ``OnChildChange``,
``OnChildrenChange``, ``OnDescendantsChange``,
``OnPrimitiveChange``) live in ``nu.core.reactive``: one unified
interface for all substrates, reached through the shape Form mixins.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from nu.engine.structure import Declared
from nu.lang import Command, ScalarQuery
from nu.lang.null import is_null


if TYPE_CHECKING:
    from collections.abc import Callable

    from nu.lang.runtime import Runtime

__all__ = [
    "AdvanceCursor",
    "Erase",
    "Exists",
    "Extract",
    "Load",
    "PrimitiveSet",
    "SetCmd",
]


# ---------------------------------------------------------------------------
# Read queries
# ---------------------------------------------------------------------------


class Load(ScalarQuery):
    """Yield the value at the slot-0 Ref; NULL if the address holds nothing."""

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


class Exists(ScalarQuery):
    """Yield True if the slot-0 Ref's address holds a value. Always a bool.

    Asks the ref itself (:meth:`StructuredRef._exists` / ``_aexists``). By
    default a ref holds a value when its read is not NULL; a fabric whose
    read never is NULL (a lazy container handle) answers its own way.
    """

    def _compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        ref = self._children[0]

        def thunk(rt: Runtime) -> bool:
            return bool(ref._exists(rt, rt.program.children[nid][0]))

        return thunk

    def _acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        ref = self._children[0]

        async def athunk(rt: Runtime) -> bool:
            return bool(await ref._aexists(rt, rt.program.children[nid][0]))

        return athunk


class Extract(ScalarQuery):
    """Yield the full subtree at the slot-0 Ref as a plain Python value.

    Distinct from ``Load`` in intent: Load yields the value at the Ref's
    address, Extract the whole subtree as plain data. A mem Ref, or any
    Form, already reads plain data, so the read is yielded as it is. A
    fabric whose read is a lazy handle gives its refs their own ``extract``.
    """

    def _compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        (ref_thunk,) = children

        def thunk(rt: Runtime) -> object:
            return ref_thunk(rt)

        return thunk

    def _acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        (ref_thunk,) = children

        async def athunk(rt: Runtime) -> object:
            return await ref_thunk(rt)

        return athunk


class AdvanceCursor(ScalarQuery):
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
            if is_null(cursor):
                cursor = None
            return view.next_key_after(cursor)

        return thunk

    def _acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        source_thunk, cursor_thunk = children[0], children[1]

        async def athunk(rt: Runtime) -> object:
            view = await source_thunk(rt)
            cursor = await cursor_thunk(rt)
            if is_null(cursor):
                cursor = None
            return view.next_key_after(cursor)

        return athunk


# ---------------------------------------------------------------------------
# Write commands
# ---------------------------------------------------------------------------


class SetCmd(Command):
    """Write the slot-1 value to the slot-0 structured Ref's address."""

    _mutates = Declared(value=frozenset({0}), name="mutates")

    def _compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        ref = self._children[0]
        value = children[1]

        def thunk(rt: Runtime) -> None:
            v = value(rt)
            if is_null(v):
                raise ValueError("cannot store NULL")
            ref._write(rt, v, rt.program.children[nid][0])

        return thunk

    def _acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        ref = self._children[0]
        value = children[1]

        async def athunk(rt: Runtime) -> None:
            v = await value(rt)
            if is_null(v):
                raise ValueError("cannot store NULL")
            await ref._awrite(rt, v, rt.program.children[nid][0])

        return athunk


class Erase(Command):
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


class PrimitiveSet(Command):
    """Write the slot-1 value to the slot-0 Ref via ``_primitive_write``.

    Bypasses the compound-value decomposition of ``SetCmd`` (which
    recurses into containers).  Use for Refs that store compound values as a
    single opaque blob (e.g. ``PrimitiveDictRef``, ``PrimitiveListRef``,
    ``PrimitiveSetRef`` substrates).

    Raises ``ValueError`` when the value slot evaluates to NULL,
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
            if is_null(v):
                raise ValueError("cannot store NULL")
            ref._primitive_write(rt, v, rt.program.children[nid][0])  # type: ignore[attr-defined]

        return thunk

    def _acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        ref = self._children[0]
        value = children[1]

        async def athunk(rt: Runtime) -> None:
            v = await value(rt)
            if is_null(v):
                raise ValueError("cannot store NULL")
            await ref._aprimitive_write(rt, v, rt.program.children[nid][0])  # type: ignore[attr-defined]

        return athunk
