"""Ref -- base class for all document-model refs.

Ref captures invariants shared by all Shape-aware refs:
- Hierarchical addressing (address + parent chain)
- Path composition and resolution
- Shape context association
- Slot factory protocol

Hierarchy:
    everyabc.Ref[T]              # Pure protocol: resolve, fetch, execute
        |
    eb_shape.Ref[T]            # Document-model base (this module)
        |
    ItemRef, MappingRef, etc.    # Structural types (eb_shape.refs)
        |
    eb_pv.RefBase, etc.       # Substrate implementations
"""

from __future__ import annotations

from abc import abstractmethod
from typing import TYPE_CHECKING, Self

from everybase import Ref as RefABC
from everybase import Term
from everybase.abc import AnyValue, ensure_term


if TYPE_CHECKING:
    from collections.abc import Iterable

    from everybase import Context

    from ..shape import Shape


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
    - eb_pv.RefBase: PV view navigation

    Attributes:
        address: Location identifier within parent
        parent: Parent ref for path composition
        shape: Owning Shape class for context lookup
    """

    def __init__(
        self,
        address: object,
        parent: Ref | None = None,
        owner_shape: type[Shape] | None = None,
    ) -> None:
        """Initialize ref.

        Args:
            address: Address of this filed in parent's domain
            parent: Parent reference in navigation chain
            owner_shape: Shape class this ref belongs to
        """
        try:
            address_term = ensure_term(address)
        except TypeError:
            address_term = AnyValue(address)

        super().__init__(address_term)
        self._parent = parent
        self._owner_shape = owner_shape

    # =========================================================================
    # CORE PROPERTIES — Location Identity
    # =========================================================================

    @property
    def address(self) -> Term[object]:
        """Location identifier within parent.

        Can be:
        - str: named field in a shape/dict
        - int: index in a sequence
        - Term: computed address (resolved at execution time)
        - None: root ref with no address
        """
        return self.children[0]

    @property
    def parent(self) -> Ref | None:
        """Parent ref in the navigation hierarchy.

        None for root refs (entry points from Storage).
        """
        return self._parent

    @property
    def owner_shape(self) -> type[Shape] | None:
        """Owning Shape class for context lookup.

        Used to retrieve Context handler at execution time.
        """
        return self._owner_shape

    def get_root_shape(self) -> type[Shape] | None:
        """Walk up parent chain to find the root shape.

        Returns the shape of the topmost ref in the hierarchy.
        Used to look up the correct context handle for storage access.
        """
        if self._parent is not None:
            return self._parent.get_root_shape()
        return self._owner_shape

    # =========================================================================
    # PATH COMPOSITION — Building Full Paths
    # =========================================================================

    async def resolve_address(self, ctx: Context) -> object:
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
    # RESOLUTION
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

    @abstractmethod
    async def resolve(self, ctx: Context) -> Iterable:
        """Resolve returns an iterable identifier (full chain of parents + self).

        Args:
            ctx: Execution context

        Returns:
            Value reference
        """
        ...

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
            return f"<{self.__class__.__name__}: {self._parent!r} -> {self.children[0]!r}>"
        return f"<{self.__class__.__name__}: {self.children[0]!r}>"

    def __str__(self) -> str:
        """String representation showing address and parent chain."""
        if self._parent:
            return f"{self.__class__.__name__}({self._parent!s} -> {self.children[0]!s})"
        return f"{self.__class__.__name__}({self.children[0]!s})"
