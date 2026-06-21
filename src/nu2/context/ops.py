"""Write interactions over the Context attrs fabric.

A Command names a target Ref in its mutation slot and the Fabric carries out
the write. These delegate to the Ref (``ref.write`` / ``ref.erase``) so the
write mechanism lives with the fabric (the Ref), not hardcoded here - the same
``Set`` works for any fabric whose Ref implements the write contract.

The mutation slot holds the Ref; every other slot is a read. ``mutates``
declares slot 0 so the effect synthesis binds it as a WRITE. The Ref resolves
its own address (static or dynamic), so the Command passes it the Ref's node id
and never touches the address itself.

v1 reference: ``src/nu/context/attr_ops.py``, ``src/nu/shapes/commands/item.py``.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from nu2.engine.structure import Declared
from nu2.lang import Command
from nu2.lang.sentinels import EMPTY, INVALID


if TYPE_CHECKING:
    from collections.abc import Callable

    from nu2.lang.runtime import Runtime

__all__ = ["Delete", "Set"]


class Set(Command):
    """Writes the value of slot 1 to the Ref in slot 0, through that Ref."""

    mutates = Declared(value=frozenset({0}))

    def compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:  # noqa: D102
        ref = self.children[0]
        value = children[1]

        def thunk(rt: Runtime) -> None:
            v = value(rt)
            if v is EMPTY or v is INVALID:
                return
            ref.write(rt, v, rt.program.children[nid][0])

        return thunk

    def acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:  # noqa: D102
        ref = self.children[0]
        value = children[1]

        async def athunk(rt: Runtime) -> None:
            v = await value(rt)
            if v is EMPTY or v is INVALID:
                return
            await ref.awrite(rt, v, rt.program.children[nid][0])

        return athunk


class Delete(Command):
    """Removes the Ref in slot 0 from its fabric, through that Ref."""

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
