"""_StructuredRef: abstract base for all shape-fabric Refs.

A _StructuredRef encodes a hierarchical path into a shape fabric.
Each Ref holds its address as children[0] (resolved via the runtime like any
other child thunk) and a back-pointer to its parent Ref stored as
``_parent_ref`` — NOT as tree children[1].

``address`` / ``aaddress`` mirror the context/refs.py pattern:
    rt.eval(rt.program.children[nid][0])

Substrate plug-points (``afetch_parent``, ``aresolve_address``) carry their
signatures and raise NotImplementedError; substrate implementations
extend concrete subclasses and override these. ``compile`` / ``acompile``
are also left to substrate subclasses (or blueprint Refs used purely for
structural navigation).
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from nu.lang import Ref


if TYPE_CHECKING:
    from nu.domains.shape.dsl import Shape
    from nu.lang.runtime import Runtime

__all__ = ["_StructuredRef"]


class _StructuredRef(Ref):
    """Abstract base for shape-fabric Refs.

    Address is children[0]; parent chain is ``_parent_ref``, not children[1].
    """

    def __init__(
        self,
        address: object,
        *,
        parent_ref: _StructuredRef | None = None,
        owner_shape: type[Shape] | None = None,
    ) -> None:
        super().__init__(address)
        self._parent_ref = parent_ref
        self._owner_shape = owner_shape
        self._root_shape: type[Shape] | None = (
            parent_ref._root_shape if parent_ref is not None else owner_shape
        )

    # --- navigation properties -----------------------------------------------

    @property
    def parent_ref(self) -> _StructuredRef | None:
        """Parent Ref in the navigation chain; None for root Refs."""
        return self._parent_ref

    @property
    def owner_shape(self) -> type[Shape] | None:
        """Shape class that directly owns this slot."""
        return self._owner_shape

    def get_root_shape(self) -> type[Shape] | None:
        """Return the root Shape for this Ref chain (cached at construction)."""
        return self._root_shape

    # --- address resolution --------------------------------------------------

    def address(self, rt: Runtime, nid: int) -> object:
        """Resolve this Ref's address; nid is the Ref's own node id."""
        return rt.eval(rt.program.children[nid][0])

    async def aaddress(self, rt: Runtime, nid: int) -> object:
        """Async sibling of :meth:`address`."""
        return await rt.aeval(rt.program.children[nid][0])

    # --- substrate plug-points (deferred) ------------------------------------

    async def afetch_parent(self, rt: Runtime, nid: int) -> object:
        """Fetch the parent container holding this Ref's slot. Substrate-specific."""
        msg = f"{type(self).__name__}.afetch_parent is not implemented"
        raise NotImplementedError(msg)

    async def aresolve_address(self, rt: Runtime, nid: int) -> object:
        """Resolve this segment's address against the runtime. Substrate-specific."""
        msg = f"{type(self).__name__}.aresolve_address is not implemented"
        raise NotImplementedError(msg)

    def _primitive_write(self, rt: Runtime, value: object, nid_self: int) -> None:
        """Write ``value`` as a single primitive blob, bypassing compound decomposition.

        Override in substrates that support primitive-blob storage
        (e.g. PrimitiveDictRef, PrimitiveListRef, PrimitiveSetRef).
        Called by ``PrimitiveStoreCommand``.
        """
        msg = f"{type(self).__name__}._primitive_write is not implemented"
        raise NotImplementedError(msg)

    async def _aprimitive_write(self, rt: Runtime, value: object, nid_self: int) -> None:
        """Async sibling of :meth:`_primitive_write`."""
        msg = f"{type(self).__name__}._aprimitive_write is not implemented"
        raise NotImplementedError(msg)

    # --- value coercion (storage → domain) -----------------------------------

    def coerce(self, raw: object) -> object:
        """Convert a raw storage value to its domain type.

        Identity by default; substrates override when storage representation
        differs from the domain type (e.g. ISO string → datetime).
        Called in substrate ``fetch`` / ``afetch`` after reading the raw value.
        """
        return raw

    async def acoerce(self, raw: object) -> object:
        """Async sibling of :meth:`coerce`. Identity by default."""
        return raw

    # --- repr ----------------------------------------------------------------

    def __repr__(self) -> str:
        parent = self._parent_ref
        addr = self.children[0] if self.children else None
        if parent:
            return f"<{type(self).__name__}: {parent!r} -> {addr!r}>"
        return f"<{type(self).__name__}: {addr!r}>"
