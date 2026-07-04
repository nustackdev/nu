"""Write interactions over the Context attrs fabric.

A Command names a target Ref in its mutation slot and the Fabric carries out
the write. These delegate to the Ref (``ref._write`` / ``ref._erase``) so the
write mechanism lives with the fabric (the Ref), not hardcoded here - the same
``SetCommand`` works for any fabric whose Ref implements the write contract.

The mutation slot holds the Ref; every other slot is a read. ``mutates``
declares slot 0 so the effect synthesis binds it as a WRITE. The Ref resolves
its own address (static or dynamic), so the Command passes it the Ref's node id
and never touches the address itself.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from nu.engine.structure import Declared
from nu.lang import Command
from nu.lang.sentinels import EMPTY, INVALID


if TYPE_CHECKING:
    from collections.abc import Callable

    from nu.lang.runtime import Runtime

__all__ = ["DeleteCommand", "SetCommand"]


class SetCommand(Command):
    """Writes the value of slot 1 to the Ref in slot 0, through that Ref."""

    mutates = Declared(value=frozenset({0}))

    def compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:  # noqa: D102
        ref = self.children[0]
        value = children[1]

        def thunk(rt: Runtime) -> None:
            v = value(rt)
            if v is EMPTY or v is INVALID:
                return
            ref._write(rt, v, rt.program.children[nid][0])

        return thunk

    def acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:  # noqa: D102
        ref = self.children[0]
        value = children[1]

        async def athunk(rt: Runtime) -> None:
            v = await value(rt)
            if v is EMPTY or v is INVALID:
                return
            await ref._awrite(rt, v, rt.program.children[nid][0])

        return athunk


class DeleteCommand(Command):
    """Removes the Ref in slot 0 from its fabric, through that Ref."""

    mutates = Declared(value=frozenset({0}))

    def compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:  # noqa: D102
        ref = self.children[0]

        def thunk(rt: Runtime) -> None:
            ref._erase(rt, rt.program.children[nid][0])

        return thunk

    def acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:  # noqa: D102
        ref = self.children[0]

        async def athunk(rt: Runtime) -> None:
            await ref._aerase(rt, rt.program.children[nid][0])

        return athunk
