"""Virtuals item interactions — unsafe leaf read/write/delete + container setup.

EnsureLayoutCmd: Materialize view container layout (idempotent setup).
InitItemCmd: Materialize container chain via _fetch().
ItemPrimitiveGetUnsafe: Read — _unsafe_primitive_read() (single ctx.get).
ItemPrimitiveSetUnsafeCmd: Write — _unsafe_primitive_write(ensure_exists=True).
ItemPrimitiveSetUnsafeParentSkipCmd: Write — _unsafe_primitive_write() (full skip).
ItemPrimitiveDeleteUnsafeCmd: Delete — _unsafe_primitive_delete().
ItemPrimitiveStoreCmd: Store value via _primitive_write() — bypasses container check.

All named explicitly Unsafe — optimization internals for tree deformers, not
user-facing APIs. They require virtuals views with UnsafePrimitiveOpsBase in MRO.
The leaf ref is held as ``children[0]`` (a virtuals Ref / FlatRef), so its
substrate methods take ``(rt, nid)``.
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
    "EnsureLayoutCmd",
    "InitItemCmd",
    "ItemPrimitiveDeleteUnsafeCmd",
    "ItemPrimitiveGetUnsafe",
    "ItemPrimitiveSetUnsafeCmd",
    "ItemPrimitiveSetUnsafeParentSkipCmd",
    "ItemPrimitiveStoreCmd",
]


def _child_nid(rt: Runtime, nid: int, slot: int) -> int:
    return rt.program.children[nid][slot]


class EnsureLayoutCmd(Command):
    """Ensure a view container and its internal layout exist in storage.

    Navigates to the view via the ref's ``fetch`` thunk, then calls
    ``_ensure_layout()`` (or ``ensure_created()``) to create internal containers.
    """

    _mutates = Declared(value=frozenset({0}), name="mutates")

    def _compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:  # noqa: D102
        ref = self._children[0]

        def thunk(rt: Runtime) -> None:
            view = ref._fetch(rt, _child_nid(rt, nid, 0))
            if hasattr(view, "_ensure_layout"):
                view._ensure_layout()
            elif hasattr(view, "ensure_created"):
                view.ensure_created()

        return thunk

    def _acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:  # noqa: D102
        ref = self._children[0]

        async def athunk(rt: Runtime) -> None:
            view = await ref._afetch(rt, _child_nid(rt, nid, 0))
            if hasattr(view, "_ensure_layout"):
                view._ensure_layout()
            elif hasattr(view, "ensure_created"):
                view.ensure_created()

        return athunk


class InitItemCmd(Command):
    """Materialize the container chain for a ViewRef via ``fetch``."""

    _mutates = Declared(value=frozenset({0}), name="mutates")

    def _compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:  # noqa: D102
        ref = self._children[0]

        def thunk(rt: Runtime) -> None:
            ref._fetch(rt, _child_nid(rt, nid, 0))

        return thunk

    def _acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:  # noqa: D102
        ref = self._children[0]

        async def athunk(rt: Runtime) -> None:
            await ref._afetch(rt, _child_nid(rt, nid, 0))

        return athunk


class ItemPrimitiveGetUnsafe(ScalarQuery):
    """Read a primitive value via ``_unsafe_primitive_read`` (single ctx.get)."""

    def _compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:  # noqa: D102
        ref = self._children[0]

        def thunk(rt: Runtime) -> object:
            cnid = _child_nid(rt, nid, 0)
            parent = ref._fetch_parent_view(rt, ref._resolve_path(rt, cnid))
            address = ref._address(rt, cnid)
            value = parent._unsafe_primitive_read(address)
            return EMPTY if value is EMPTY or value is INVALID else value

        return thunk

    def _acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:  # noqa: D102
        ref = self._children[0]

        async def athunk(rt: Runtime) -> object:
            cnid = _child_nid(rt, nid, 0)
            parent = ref._fetch_parent_view(rt, await ref._aresolve_path(rt, cnid))
            address = await ref._aaddress(rt, cnid)
            value = parent._unsafe_primitive_read(address)
            return EMPTY if value is EMPTY or value is INVALID else value

        return athunk


class _UnsafeSetBase(Command):
    """Shared base: resolve parent view + address + value, then unsafe-write."""

    _mutates = Declared(value=frozenset({0}), name="mutates")
    _ensure_exists: bool = False

    def _compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        ref = self._children[0]
        value_thunk = children[1]
        ensure = self._ensure_exists

        def thunk(rt: Runtime) -> None:
            cnid = _child_nid(rt, nid, 0)
            parent = ref._fetch_parent_view(rt, ref._resolve_path(rt, cnid))
            address = ref._address(rt, cnid)
            value = value_thunk(rt)
            if value is EMPTY or value is INVALID:
                raise ValueError("cannot store sentinel value")
            parent._unsafe_primitive_write(address, value, ensure_exists=ensure)

        return thunk

    def _acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        ref = self._children[0]
        value_thunk = children[1]
        ensure = self._ensure_exists

        async def athunk(rt: Runtime) -> None:
            cnid = _child_nid(rt, nid, 0)
            parent = ref._fetch_parent_view(rt, await ref._aresolve_path(rt, cnid))
            address = await ref._aaddress(rt, cnid)
            value = await value_thunk(rt)
            if value is EMPTY or value is INVALID:
                raise ValueError("cannot store sentinel value")
            parent._unsafe_primitive_write(address, value, ensure_exists=ensure)

        return athunk


class ItemPrimitiveSetUnsafeCmd(_UnsafeSetBase):
    """Write primitive via ``_unsafe_primitive_write(ensure_exists=True)``."""

    _ensure_exists = True


class ItemPrimitiveSetUnsafeParentSkipCmd(_UnsafeSetBase):
    """Write primitive via ``_unsafe_primitive_write()`` — full skip."""

    _ensure_exists = False


class ItemPrimitiveDeleteUnsafeCmd(Command):
    """Delete primitive via ``_unsafe_primitive_delete()``."""

    _mutates = Declared(value=frozenset({0}), name="mutates")

    def _compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:  # noqa: D102
        ref = self._children[0]

        def thunk(rt: Runtime) -> None:
            cnid = _child_nid(rt, nid, 0)
            parent = ref._fetch_parent_view(rt, ref._resolve_path(rt, cnid))
            parent._unsafe_primitive_delete(ref._address(rt, cnid))

        return thunk

    def _acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:  # noqa: D102
        ref = self._children[0]

        async def athunk(rt: Runtime) -> None:
            cnid = _child_nid(rt, nid, 0)
            parent = ref._fetch_parent_view(rt, await ref._aresolve_path(rt, cnid))
            parent._unsafe_primitive_delete(await ref._aaddress(rt, cnid))

        return athunk


class ItemPrimitiveStoreCmd(Command):
    """Store a value via ``_primitive_write()``, bypassing container type checks."""

    _mutates = Declared(value=frozenset({0}), name="mutates")

    def _compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:  # noqa: D102
        ref = self._children[0]
        data_thunk = children[1]

        def thunk(rt: Runtime) -> None:
            data = data_thunk(rt)
            if data is EMPTY or data is INVALID:
                raise ValueError("cannot store sentinel value")
            cnid = _child_nid(rt, nid, 0)
            parent = ref._fetch_parent_view(rt, ref._resolve_path(rt, cnid))
            parent._primitive_write(ref._address(rt, cnid), data)

        return thunk

    def _acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:  # noqa: D102
        ref = self._children[0]
        data_thunk = children[1]

        async def athunk(rt: Runtime) -> None:
            data = await data_thunk(rt)
            if data is EMPTY or data is INVALID:
                raise ValueError("cannot store sentinel value")
            cnid = _child_nid(rt, nid, 0)
            parent = ref._fetch_parent_view(rt, await ref._aresolve_path(rt, cnid))
            parent._primitive_write(await ref._aaddress(rt, cnid), data)

        return athunk
