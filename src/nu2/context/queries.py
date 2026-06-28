"""Read queries over the Context fabric: existence checks.

The value read is the Ref itself (the dual role) - ``AttrRef`` self-yields the
value at its address, ``ServiceRef`` the bound service. What the dual role does
*not* cover is asking whether an address is bound at all, since an unbound read
yields EMPTY, which a bound EMPTY would alias. These queries answer that:

- ``AttrExistsQuery`` - is the ``AttrRef``'s address bound in ``ctx.attrs``?
- ``ServiceExistsQuery`` - is the ``ServiceRef``'s service type bound in ``ctx``?

Each holds its Ref in a read slot, so the effect synthesis binds it as a READ
on that Ref's fabric. The query needs the Ref's *address* (not its value), so
it resolves through the Ref the way the write ops do.

v1 reference: ``src/nu/context/attr_ops.py``, ``src/nu/context/service_ops.py``.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from nu2.lang import ScalarQuery


if TYPE_CHECKING:
    from collections.abc import Callable

    from nu2.lang.runtime import Runtime

__all__ = ["AttrExistsQuery", "ServiceExistsQuery"]


class AttrExistsQuery(ScalarQuery):
    """Yields whether the slot-0 ``AttrRef``'s address is bound in ``ctx.attrs``."""

    def compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:  # noqa: D102
        ref = self.children[0]

        def thunk(rt: Runtime) -> object:
            address = ref.address(rt, rt.program.children[nid][0])
            return address in rt.ctx.attrs

        return thunk

    def acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:  # noqa: D102
        ref = self.children[0]

        async def athunk(rt: Runtime) -> object:
            address = await ref.aaddress(rt, rt.program.children[nid][0])
            return address in rt.ctx.attrs

        return athunk


class ServiceExistsQuery(ScalarQuery):
    """Yields whether the slot-0 ``ServiceRef``'s service type is bound."""

    def compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:  # noqa: D102
        ref = self.children[0]

        def thunk(rt: Runtime) -> object:
            return rt.ctx.has(ref.address(rt, rt.program.children[nid][0]))

        return thunk

    def acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:  # noqa: D102
        ref = self.children[0]

        async def athunk(rt: Runtime) -> object:
            return rt.ctx.has(await ref.aaddress(rt, rt.program.children[nid][0]))

        return athunk
