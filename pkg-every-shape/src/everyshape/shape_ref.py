"""ShapeRef -- base class for all document-model refs.

ShapeRef captures invariants shared by all Shape-aware refs:
- Hierarchical addressing (address + parent chain)
- Path composition and resolution
- Shape context association
- Slot factory protocol

Hierarchy:
    everyabc.Ref[T]              # Pure protocol: resolve, fetch, execute
        ↓
    ShapeRef[T]                  # Document-model base (this module)
        ↓
    ItemRef, MappingRef, etc.    # Structural types (items.py, collections.py)
        ↓
    every_pv.RefBase, etc.       # Substrate implementations
"""

from __future__ import annotations

from abc import abstractmethod
from typing import TYPE_CHECKING, Self

from everyabc import Ref, Term


if TYPE_CHECKING:
    from everyabc import Context

    from .shape import Shape as ShapeBase


__all__ = [
    "ShapeRef",
]


class ShapeRef[T](Ref[T]):
    """Base for all document-model refs.

    Captures invariants shared by all Shape-aware refs:
    - Hierarchical addressing (address + parent chain)
    - Path composition and resolution
    - Shape context association
    - Slot factory protocol

    Substrates extend this with storage-specific mechanics:
    - every_dict.RefBase: dict navigation
    - every_pv.RefBase: PV view navigation

    Properties (abstract, set by __init__):
        address: Location identifier within parent
        parent: Parent ref for path composition
        shape: Owning Shape class for context lookup
    """

    # =========================================================================
    # CORE PROPERTIES — Location Identity
    # =========================================================================

    @property
    @abstractmethod
    def address(self) -> str | int | Term:
        """Location identifier within parent.

        Can be:
        - str: named field in a shape/dict
        - int: index in a sequence
        - Term: computed address (resolved at execution time)
        """
        ...

    @property
    @abstractmethod
    def parent(self) -> ShapeRef | None:
        """Parent ref in the navigation hierarchy.

        None for root refs (entry points from Storage).
        """
        ...

    @property
    @abstractmethod
    def shape(self) -> type[ShapeBase] | None:
        """Owning Shape class for context lookup.

        Used to find the right Storage handle at execution time.
        """
        ...

    # =========================================================================
    # PATH COMPOSITION — Building Full Paths
    # =========================================================================

    async def resolve_address(self, ctx: Context) -> str | int:
        """Resolve this segment's address to concrete value.

        Handles dynamic (Term) addresses by executing them.

        Args:
            ctx: Execution context

        Returns:
            Resolved address (str for keys, int for indices)
        """
        addr = self.address
        if isinstance(addr, Term):
            return await addr.execute(ctx)
        return addr

    def get_root_shape(self) -> type[ShapeBase] | None:
        """Traverse parent chain to find root shape.

        Used when a nested ref needs the storage context.

        Returns:
            Root shape class, or None if no shape in chain.
        """
        if self.shape is not None:
            return self.shape
        if self.parent is not None:
            return self.parent.get_root_shape()
        return None

    def get_path_segments(self) -> list[ShapeRef]:
        """Get all refs from root to self (inclusive).

        Returns list starting from root, ending with self.
        Useful for debugging and path visualization.

        Returns:
            List of ShapeRefs from root to self.
        """
        segments: list[ShapeRef] = []
        current: ShapeRef | None = self
        while current is not None:
            segments.append(current)
            current = current.parent
        return list(reversed(segments))

    # =========================================================================
    # PARENT CONTAINER ACCESS
    # =========================================================================

    @abstractmethod
    async def fetch_parent(self, ctx: Context) -> object:
        """Fetch the parent container holding this ref's value.

        Returns the dict/list/view that contains this ref's slot.
        Returns storage root if this is a root ref.

        Args:
            ctx: Execution context

        Returns:
            Parent container (substrate-specific type)
        """
        ...

    # =========================================================================
    # SLOT FACTORY — Creating Slots for Shape Definitions
    # =========================================================================

    @classmethod
    @abstractmethod
    def slot(cls) -> Self:
        """Create a Slot that produces instances of this Ref.

        Contract: Every ShapeRef subclass provides its own .slot()
        with substrate-specific typed signature for IDE autocomplete.

        Example (PV substrate):
            @classmethod
            def slot(cls, view_type: type[View] = DictView) -> PVIntRef:
                return Slot(cls, view_type=view_type)

        Example (Dict substrate):
            @classmethod
            def slot(cls) -> DictIntRef:
                return Slot(cls)

        Returns:
            Slot instance (typed as Self for IDE support)
        """
        ...

    # =========================================================================
    # REPR / DEBUG
    # =========================================================================

    def __repr__(self) -> str:
        """Debug representation showing address and parent chain depth."""
        depth = len(self.get_path_segments())
        return f"<{self.__class__.__name__} address={self.address!r} depth={depth}>"
