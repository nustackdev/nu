"""Attr-fabric interactions: ``SetCommand``, ``DeleteCommand``, ``AttrExistsQuery``.

The write ops (``SetCommand`` / ``DeleteCommand``) delegate to the Ref
(``ref._write`` / ``ref._erase``) so the write mechanism lives with the fabric,
not hardcoded here. ``AttrExistsQuery`` complements the dual-role read: an
unbound read yields EMPTY, which a bound EMPTY would alias, so existence needs
an explicit query.

Each holds its Ref in a mutation or read slot; effect synthesis binds it to the
right effect on the attrs fabric.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from nu.engine.structure import Declared
from nu.lang import Command, ScalarQuery
from nu.lang.sentinels import EMPTY, INVALID


if TYPE_CHECKING:
    from collections.abc import Callable

    from nu.lang.runtime import Runtime


__all__ = ["AttrExistsQuery", "DeleteCommand", "SetCommand"]


class SetCommand(Command):
    """Writes the value of slot 1 to the Ref in slot 0, through that Ref."""

    _mutates = Declared(value=frozenset({0}), name="mutates")

    def _compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:  # noqa: D102
        ref = self._children[0]
        value = children[1]

        def thunk(rt: Runtime) -> None:
            v = value(rt)
            if v is EMPTY or v is INVALID:
                return
            ref._write(rt, v, rt.program.children[nid][0])

        return thunk

    def _acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:  # noqa: D102
        ref = self._children[0]
        value = children[1]

        async def athunk(rt: Runtime) -> None:
            v = await value(rt)
            if v is EMPTY or v is INVALID:
                return
            await ref._awrite(rt, v, rt.program.children[nid][0])

        return athunk


class DeleteCommand(Command):
    """Removes the Ref in slot 0 from its fabric, through that Ref."""

    _mutates = Declared(value=frozenset({0}), name="mutates")

    def _compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:  # noqa: D102
        ref = self._children[0]

        def thunk(rt: Runtime) -> None:
            ref._erase(rt, rt.program.children[nid][0])

        return thunk

    def _acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:  # noqa: D102
        ref = self._children[0]

        async def athunk(rt: Runtime) -> None:
            await ref._aerase(rt, rt.program.children[nid][0])

        return athunk


class AttrExistsQuery(ScalarQuery):
    """Yields whether the slot-0 ``AttrRef``'s address is bound in ``ctx.attrs``."""

    def _compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:  # noqa: D102
        ref = self._children[0]

        def thunk(rt: Runtime) -> object:
            address = ref._address(rt, rt.program.children[nid][0])
            return address in rt.ctx.attrs

        return thunk

    def _acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:  # noqa: D102
        ref = self._children[0]

        async def athunk(rt: Runtime) -> object:
            address = await ref._aaddress(rt, rt.program.children[nid][0])
            return address in rt.ctx.attrs

        return athunk
