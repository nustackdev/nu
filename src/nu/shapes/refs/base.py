"""Ref -- base class for all document-model refs.

Ref captures invariants shared by all Shape-aware refs:
- Hierarchical addressing (address + parent chain)
- Path composition and resolution
- Shape context association
- Slot factory protocol

Tree structure:
    children[0] = address Nu (always present)
    children[1] = parent ref (present when parent is not None)

The parent ref is a tree child so that tree traversal (find, preorder)
naturally discovers the full ref chain — including cross-scope address
dependencies like ``PersShape.tokens[MemShape.cursor]``.

Hierarchy:
    everyabc.Ref[T]              # Pure protocol: resolve, fetch, execute
        |
    everyshape.Ref[T]            # Document-model base (this module)
        |
    ItemRef, MappingRef, etc.    # Structural types (everyshape.refs)
        |
    eb_virtuals.RefBase, etc.       # Substrate implementations
"""

from __future__ import annotations

from abc import abstractmethod
from typing import TYPE_CHECKING, Self

from nu import Ref as RefABC
from nu import Nu
from nu.interfaces.values import AnyValue
from nu.utils import ensure_nu


if TYPE_CHECKING:
    from collections.abc import Iterable

    from nu import Context

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

    Tree children:
        children[0]: address Nu — location within parent
        children[1]: parent ref — parent in navigation chain (if any)

    Substrates extend this with storage-specific mechanics:
    - eb_virtuals.RefBase: PV view navigation

    Attributes:
        address: Location identifier within parent (children[0])
        parent: Parent ref for path composition (children[1] or None)
        owner_shape: Owning Shape class for context lookup
    """

    def __init__(
        self,
        *,
        address: object,
        parent: Ref | None = None,
        owner_shape: type[Shape] | None = None,
        **kwargs: object,
    ) -> None:
        """Initialize ref.

        Args:
            address: Address of this field in parent's domain
            parent: Parent reference in navigation chain
            owner_shape: Shape class this ref belongs to
            **kwargs: Passed to super for cooperative MRO
        """
        # Store raw address before wrapping — lets substrates detect static
        # (literal str/int) vs dynamic (Nu) addresses for fast-path optimisation.
        self._raw_address = address if not isinstance(address, Nu) else None

        try:
            address_term = ensure_nu(address)
        except TypeError:
            address_term = AnyValue(address)

        if parent is not None:
            super().__init__(address_term, parent)
        else:
            super().__init__(address_term)
        self._owner_shape = owner_shape

        # Cache root shape — identical for entire ref chain, avoids O(depth) walk.
        self._root_shape: type[Shape] | None = (
            parent._root_shape if parent is not None else owner_shape
        )

    # =========================================================================
    # CORE PROPERTIES — Location Identity
    # =========================================================================

    @property
    def address(self) -> Nu[object]:
        """Location identifier within parent.

        Can be:
        - str: named field in a shape/dict
        - int: index in a sequence
        - Nu: computed address (resolved at execution time)
        - None: root ref with no address
        """
        return self.children[0]

    @property
    def parent(self) -> Ref | None:
        """Parent ref in the navigation hierarchy.

        None for root refs (entry points from Storage).
        Stored as children[1] in the tree.
        """
        if len(self.children) > 1:
            return self.children[1]
        return None

    @property
    def owner_shape(self) -> type[Shape] | None:
        """Owning Shape class for context lookup.

        Used to retrieve Context handler at execution time.
        """
        return self._owner_shape

    def get_root_shape(self) -> type[Shape] | None:
        """Return root shape (cached at construction time).

        Returns the shape of the topmost ref in the hierarchy.
        Used to look up the correct context handle for storage access.
        """
        return self._root_shape

    # =========================================================================
    # PATH COMPOSITION — Building Full Paths
    # =========================================================================

    async def resolve_address(self, ctx: Context) -> object:
        """Resolve this segment's address to concrete value.

        Handles dynamic (Nu) addresses by executing them.

        Args:
            ctx: Execution context

        Returns:
            Resolved address (str for keys, int for indices)
        """
        addr = self.address
        if isinstance(addr, Nu):
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
    # VALUE COERCION — Storage → Domain conversion
    # =========================================================================

    def coerce(self, raw: object) -> object:
        """Convert raw storage value to domain type.

        Called by substrate ``fetch()`` after reading the raw value.
        Default is identity (return as-is). Override in custom types
        to convert storage representation to domain objects.

        Example (datetime stored as ISO string)::

            def coerce(self, raw: str) -> datetime:
                return datetime.fromisoformat(raw)
        """
        return raw

    # =========================================================================
    # REPR / DEBUG
    # =========================================================================

    def __repr__(self) -> str:
        """Debug representation showing address and parent chain."""
        parent = self.parent
        if parent:
            return f"<{self.__class__.__name__}: {parent!r} -> {self.children[0]!r}>"
        return f"<{self.__class__.__name__}: {self.children[0]!r}>"

    def __str__(self) -> str:
        """String representation showing address and parent chain."""
        parent = self.parent
        if parent:
            return f"{self.__class__.__name__}({parent!s} -> {self.children[0]!s})"
        return f"{self.__class__.__name__}({self.children[0]!s})"
