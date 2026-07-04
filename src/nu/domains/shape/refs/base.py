"""StructuredRef: abstract base for all shape-fabric Refs.

A StructuredRef encodes a hierarchical path into a shape fabric. The parent
lives IN the tree as ``children[0]`` (marked ``structural`` — address structure,
never value-read); this Ref's own address is ``children[1]`` (a value, resolved
through the runtime like any child). A chain's top Ref points ``children[0]`` at
the shared :data:`ANCHOR`, a leaf Ref that terminates the chain at the fabric
root.

This replaces the old off-tree ``_parent_ref`` back-pointer. With the parent on
the tree, every generic pass reaches the whole Ref uniformly: no ``walk_ref_chain``
bridging two worlds, and inline becomes a plain fold.

``address`` / ``aaddress`` resolve ``children[1]`` through the runtime. Substrate
plug-points (``afetch_parent``, ``aresolve_address``) carry their signatures and
raise NotImplementedError; substrate subclasses override these. ``compile`` /
``acompile`` are left to substrate subclasses (or blueprint Refs used purely for
structural navigation).
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from nu.engine import Declared
from nu.lang import EMPTY, Ref


if TYPE_CHECKING:
    from collections.abc import Callable

    from nu.domains.shape.dsl import Shape
    from nu.lang.runtime import Runtime

__all__ = ["ANCHOR", "Anchor", "StructuredRef"]


class Anchor(Ref):
    """Terminates a StructuredRef parent chain at the fabric root.

    A structural leaf: no children, no address, ``structural`` empty (it is not
    a StructuredRef). It is never value-read — it only marks where a chain's
    parent walk bottoms out. Stateless, so one shared instance (:data:`ANCHOR`)
    backs every chain root.
    """

    def compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:  # noqa: D102
        return lambda rt: EMPTY

    def acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:  # noqa: D102
        async def athunk(rt: Runtime) -> object:
            return EMPTY

        return athunk

    def __repr__(self) -> str:
        return "<Anchor>"


ANCHOR = Anchor()


class StructuredRef(Ref):
    """Abstract base for shape-fabric Refs.

    ``children[0]`` = parent (a StructuredRef, or :data:`ANCHOR` at a chain
    root), marked ``structural``. ``children[1]`` = this Ref's address (a value).
    """

    structural = Declared(value=frozenset({0}))

    def __init__(
        self,
        address: object,
        *,
        parent_ref: StructuredRef | None = None,
        owner_shape: type[Shape] | None = None,
    ) -> None:
        parent = parent_ref if parent_ref is not None else ANCHOR
        super().__init__(parent, address)
        self._owner_shape = owner_shape
        self._root_shape: type[Shape] | None = (
            parent_ref._root_shape if parent_ref is not None else owner_shape
        )

    # --- construction --------------------------------------------------------

    def with_children(self, *children: object) -> StructuredRef:  # type: ignore[override]
        """Rebuild with new children while preserving Ref navigation metadata.

        The base :class:`Term.with_children` copies only ``children`` and
        ``payload``. Shape Refs still carry non-structural navigation metadata as
        instance attrs (``_owner_shape``, ``_root_shape``, plus substrate markers
        like ``_segment``, ``_value_type``, ``_view_type``), so we copy the full
        ``__dict__`` and then override ``children``. The *parent* is no longer
        smuggled here — it lives in ``children[0]`` and rewrites like any child.
        """
        variant = object.__new__(type(self))
        variant.__dict__.update(self.__dict__)
        variant.children = children
        return variant

    # --- navigation properties -----------------------------------------------

    @property
    def _parent(self) -> StructuredRef | None:
        """Parent Ref in the navigation chain; None at a chain root (ANCHOR).

        Private: core navigation machinery, not user-facing. Underscore also keeps
        it clear of value-domain members like ``PurePath.parent`` that a typed leaf
        Ref exposes on its public surface.
        """
        p = self.children[0]
        return p if isinstance(p, StructuredRef) else None

    @property
    def owner_shape(self) -> type[Shape] | None:
        """Shape class that directly owns this slot."""
        return self._owner_shape

    def get_root_shape(self) -> type[Shape] | None:
        """Return the root Shape for this Ref chain (cached at construction)."""
        return self._root_shape

    # --- address resolution --------------------------------------------------

    def address(self, rt: Runtime, nid: int) -> object:
        """Resolve this Ref's own address (``children[1]``); nid is this node's id."""
        return rt.eval(rt.program.children[nid][1])

    async def aaddress(self, rt: Runtime, nid: int) -> object:
        """Async sibling of :meth:`address`."""
        return await rt.aeval(rt.program.children[nid][1])

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
        """Async sibling of :meth:`coerce`; delegates to it by default.

        Coercion is pure storage->domain shaping, so the async path reuses the
        sync ``coerce``. A ref overriding only ``coerce`` is therefore correct on
        both read paths; override this too only for genuinely async coercion.
        """
        return self.coerce(raw)

    # --- repr ----------------------------------------------------------------

    def __repr__(self) -> str:
        addr = self.children[1] if len(self.children) > 1 else None
        if self._parent is not None:
            return f"<{type(self).__name__} -> {addr!r}>"
        return f"<{type(self).__name__}: {addr!r}>"
