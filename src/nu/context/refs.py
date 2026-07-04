"""Context-fabric Refs: ``AttrRef`` (attrs store) and ``ServiceRef`` (bindings).

Two concrete Refs over the Context fabric. A Ref names an *address*, and an
address is just a Nu child: it is resolved through the runtime like any other
child. A bare string or type is auto-wrapped into a ``Literal`` (so
``AttrRef("total")`` carries ``Literal("total")`` as its address); a computed
address is whatever Nu term you pass. There is no special "name" - one uniform
path: resolve the address child, then run the fabric lookup.

- ``AttrRef`` - address resolves to a key into ``ctx.attrs``. Reads through the
  dual role (self-yield the value at the address); writes and erases go through
  the Ref so a Command never touches ``ctx.attrs`` itself.
- ``ServiceRef`` - address resolves to a service type, looked up in the typed
  bindings (``ctx.bind`` / ``ctx.get``). Read-only: services are bound on the
  Context, not written through a Ref.

The abstract ``Ref`` kind carries nothing; the fabric is the concrete class and
the address is the child.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, ClassVar

from nu.forms.collections import DictForm, FrozenSetForm, ListForm, SetForm, TupleForm
from nu.forms.primitives import AnyForm, BoolForm, BytesForm, FloatForm, IntForm, NoneForm, StrForm
from nu.lang import Ref
from nu.lang.sentinels import EMPTY


if TYPE_CHECKING:
    from collections.abc import Callable

    from nu.lang.runtime import Runtime

    from .queries import AttrExistsQuery, ServiceExistsQuery

__all__ = [
    "AnyAttrRef",
    "AttrRef",
    "BoolAttrRef",
    "BytesAttrRef",
    "DictAttrRef",
    "FloatAttrRef",
    "FrozenSetAttrRef",
    "IntAttrRef",
    "ListAttrRef",
    "NoneAttrRef",
    "ServiceRef",
    "SetAttrRef",
    "StrAttrRef",
    "TupleAttrRef",
]


class _ContextRef(Ref):
    """A Context Ref whose address is its sole child, resolved through the runtime.

    ``address`` / ``aaddress`` evaluate the address child given the Ref's own
    node id - the same resolution the dual-role read uses, exposed so the write
    ops can resolve the target through the Ref rather than reaching past it.
    """

    def _address(self, rt: Runtime, nid: int) -> object:
        """Resolve this Ref's address; ``nid`` is the Ref's own node id."""
        return rt.eval(rt.program.children[nid][0])

    async def _aaddress(self, rt: Runtime, nid: int) -> object:
        """Async sibling of :meth:`address`."""
        return await rt.aeval(rt.program.children[nid][0])


class AttrRef(_ContextRef):
    """A Ref into the ``ctx.attrs`` store, keyed by its resolved address.

    The address child resolves to a key. Reads yield the value at that key
    (EMPTY when unbound) through the dual role; writes and erases resolve the
    address and go through the Ref. The address can be anything that yields a
    value - ``AttrRef("total")`` (a literal key) or ``AttrRef(AttrRef("k"))``
    (a key read from another slot).
    """

    def compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:  # noqa: D102
        address = children[0]

        def thunk(rt: Runtime) -> object:
            return rt.ctx.attrs.get(address(rt), EMPTY)

        return thunk

    def acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:  # noqa: D102
        address = children[0]

        async def athunk(rt: Runtime) -> object:
            return rt.ctx.attrs.get(await address(rt), EMPTY)

        return athunk

    def _write(self, rt: Runtime, value: object, nid: int) -> None:
        """Write ``value`` to this Ref's slot in the attrs fabric."""
        rt.ctx.attrs[self._address(rt, nid)] = value

    async def _awrite(self, rt: Runtime, value: object, nid: int) -> None:
        """Async sibling of :meth:`write`."""
        rt.ctx.attrs[await self._aaddress(rt, nid)] = value

    def _erase(self, rt: Runtime, nid: int) -> None:
        """Remove this Ref's slot from the attrs fabric, if present."""
        address = self._address(rt, nid)
        if address in rt.ctx.attrs:
            del rt.ctx.attrs[address]

    async def _aerase(self, rt: Runtime, nid: int) -> None:
        """Async sibling of :meth:`erase`."""
        address = await self._aaddress(rt, nid)
        if address in rt.ctx.attrs:
            del rt.ctx.attrs[address]

    def exists(self) -> AttrExistsQuery:
        """A Query yielding whether this Ref's address is bound in ``ctx.attrs``."""
        from .queries import AttrExistsQuery

        return AttrExistsQuery(self)


class ServiceRef(_ContextRef):
    """A Ref into the Context service bindings, keyed by its resolved address.

    The address resolves to a service type; the read self-yields the bound
    service (EMPTY when unbound). Services are bound on the Context, not written
    through a Ref, so ``ServiceRef`` is read-only *as a value*.

    A service is a fabric, and each fabric is one concrete Ref class - so a
    service gets its own ``ServiceRef`` subclass carrying the bound service type
    in the ``service`` class attribute::

        class Solana(ServiceRef):
            service = SolanaClient
            slot = method_query(IntForm, "getSlot")

    ``Solana()`` then resolves ``SolanaClient`` from the Context, and its methods
    (built by the ``method_*`` descriptors / ``MethodFactory``) serialize against
    each other while staying independent of any other service. A bare
    ``ServiceRef(SolanaClient)`` still works for the untyped, one-off read.
    """

    service: ClassVar[type | None] = None

    def __init__(self, address: object = None) -> None:
        if address is None:
            address = type(self).service
            if address is None:
                msg = f"{type(self).__name__} has no bound service; pass one or set `service`"
                raise TypeError(msg)
        super().__init__(address)

    def compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:  # noqa: D102
        service = children[0]

        def thunk(rt: Runtime) -> object:
            svc = service(rt)
            return rt.ctx.get(svc) if rt.ctx.has(svc) else EMPTY

        return thunk

    def acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:  # noqa: D102
        service = children[0]

        async def athunk(rt: Runtime) -> object:
            svc = await service(rt)
            return rt.ctx.get(svc) if rt.ctx.has(svc) else EMPTY

        return athunk

    def exists(self) -> ServiceExistsQuery:
        """A Query yielding whether this Ref's service type is bound."""
        from .queries import ServiceExistsQuery

        return ServiceExistsQuery(self)


# =========================================================================
# TYPED ATTR REFS - PRIMITIVES
# =========================================================================


class IntAttrRef(AttrRef, IntForm):
    """An AttrRef with the full integer interface."""


class FloatAttrRef(AttrRef, FloatForm):
    """An AttrRef with the full float interface."""


class StrAttrRef(AttrRef, StrForm):
    """An AttrRef with the full string interface."""


class BoolAttrRef(AttrRef, BoolForm):
    """An AttrRef with the full boolean interface."""


class BytesAttrRef(AttrRef, BytesForm):
    """An AttrRef with the full bytes interface."""


class AnyAttrRef(AttrRef, AnyForm):
    """An AttrRef with the dynamic any interface."""


class NoneAttrRef(AttrRef, NoneForm):
    """An AttrRef with the none interface."""


# =========================================================================
# TYPED ATTR REFS - COLLECTIONS
# =========================================================================


class ListAttrRef(AttrRef, ListForm):
    """An AttrRef with the full list interface."""


class DictAttrRef(AttrRef, DictForm):
    """An AttrRef with the full dict interface."""


class SetAttrRef(AttrRef, SetForm):
    """An AttrRef with the full set interface."""


class FrozenSetAttrRef(AttrRef, FrozenSetForm):
    """An AttrRef with the full frozenset interface."""


class TupleAttrRef(AttrRef, TupleForm):
    """An AttrRef with the full tuple interface."""
