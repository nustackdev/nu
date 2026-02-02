"""Ref -- base class for all document-model refs.

Ref captures invariants shared by all Shape-aware refs:
- Hierarchical addressing (address + parent chain)
- Path composition and resolution
- Shape context association
- Slot factory protocol

Hierarchy:
    everyabc.Ref[T]              # Pure protocol: resolve, fetch, execute
        |
    everyshape.Ref[T]            # Document-model base (this module)
        |
    ItemRef, MappingRef, etc.    # Structural types (items.py, collections.py)
        |
    every_pv.RefBase, etc.       # Substrate implementations
"""

from __future__ import annotations

from abc import abstractmethod
from typing import TYPE_CHECKING, Self

from everyabc import Ref as RefABC
from everyabc import Term


if TYPE_CHECKING:
    from everyabc import Context

    from .shape import Shape


__all__ = [
    "Ref",
]


class Ref[T](RefABC[T]):
    """Base for all document-model refs.

    Captures invariants shared by all Shape-aware refs:
    - Hierarchical addressing (address + parent chain)
    - Path composition and resolution
    - Shape context association
    - Slot factory protocol

    Substrates extend this with storage-specific mechanics:
    - every_dict.RefBase: dict navigation
    - every_pv.RefBase: PV view navigation

    Attributes:
        _address: Location identifier within parent
        _parent: Parent ref for path composition
        _shape: Owning Shape class for context lookup
    """

    def __init__(
        self,
        address: str | int | Term | None = None,
        parent: Ref | None = None,
        shape: type[Shape] | None = None,
    ) -> None:
        """Initialize ref.

        Args:
            address: Key/index for this segment (or Term for dynamic)
            parent: Parent ref in navigation chain
            shape: Shape class for context lookup
        """
        super().__init__()
        self._address = address
        self._parent = parent
        self._shape = shape

    # =========================================================================
    # CORE PROPERTIES — Location Identity
    # =========================================================================

    @property
    def address(self) -> str | int | Term | None:
        """Location identifier within parent.

        Can be:
        - str: named field in a shape/dict
        - int: index in a sequence
        - Term: computed address (resolved at execution time)
        - None: root ref with no address
        """
        return self._address

    @property
    def parent(self) -> Ref | None:
        """Parent ref in the navigation hierarchy.

        None for root refs (entry points from Storage).
        """
        return self._parent

    @property
    def shape(self) -> type[Shape] | None:
        """Owning Shape class for context lookup.

        Used to find the right Storage handle at execution time.
        """
        return self._shape

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

    def get_root_shape(self) -> type[Shape] | None:
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

    def get_path_segments(self) -> list[Ref]:
        """Get all refs from root to self (inclusive).

        Returns list starting from root, ending with self.
        Useful for debugging and path visualization.

        Returns:
            List of Refs from root to self.
        """
        segments: list[Ref] = []
        current: Ref | None = self
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

        Contract: Every Ref subclass provides its own .slot()
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
        """Debug representation showing address and parent chain."""
        if self._parent:
            return f"<{self.__class__.__name__}: {self._parent!r} -> {self._address!r}>"
        return f"<{self.__class__.__name__}: {self._address!r}>"

    def __str__(self) -> str:
        """String representation showing address and parent chain."""
        if self._parent:
            return f"{self.__class__.__name__}({self._parent!s} -> {self._address!s})"
        return f"{self.__class__.__name__}({self._address!s})"
