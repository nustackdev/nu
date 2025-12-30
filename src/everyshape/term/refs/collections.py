"""Collection reference protocol hierarchy.

This module defines collection ref protocols composed from atomic capabilities.
Follows Python's collections.abc hierarchy while using EveryShape's capability system.

These are PROTOCOLS (type contracts) that define what refs CAN do.
Implementations live in base.py, bases.py, and refs.py.

Protocol Hierarchy:
    RefProtocol (base)
    ├── PrimitiveRefProtocol (leaf value references)
    │   └── ValueRefProtocol[T] (typed primitive value)
    └── ViewRefProtocol (container references)
        ├── SequenceRefProtocol[T] (list-like)
        │   └── MutableSequenceRefProtocol[T]
        ├── MappingRefProtocol[K,V] (dict-like)
        │   └── MutableMappingRefProtocol[K,V]
        └── SetRefProtocol[T] (set-like)
            └── MutableSetRefProtocol[T]

Similar to view/collections.py which composes view capabilities.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Protocol, runtime_checkable

from .capabilities import (
    Appendable,
    Clearable,
    Deletable,
    Existable,
    Extractable,
    Gettable,
    Insertable,
    ItemsQueryable,
    KeysQueryable,
    Lengthable,
    Nestable,
    Poppable,
    RefChildObservable,
    RefDescendantsObservable,
    RefIndexable,
    RefObservable,
    RefSliceable,
    Settable,
    Storable,
    ValuesQueryable,
)


if TYPE_CHECKING:
    from ..context import Context


__all__ = [  # noqa: RUF022
    # Base protocols
    "RefProtocol",
    # Primitive ref protocols
    "PrimitiveRefProtocol",
    "ValueRefProtocol",
    # View ref protocols
    "ViewRefProtocol",
    "SequenceRefProtocol",
    "MutableSequenceRefProtocol",
    "MappingRefProtocol",
    "MutableMappingRefProtocol",
    "SetRefProtocol",
    "MutableSetRefProtocol",
]


# =============================================================================
# BASE REF PROTOCOL
# =============================================================================


@runtime_checkable
class RefProtocol[PathT](
    Existable[object],
    Protocol,
):
    """Base protocol for all LValue references.

    All refs support:
    - Path resolution: resolve() to get storage path
    - Existence checking: exists(), missing()
    - Parent navigation: parent property

    Type Parameters:
        PathT: Type of the resolved path

    Example:
        >>> if isinstance(ref, RefProtocol):
        ...     path = ref.resolve(ctx)
        ...     exists = ref.exists().execute(ctx)
    """

    @property
    def parent(self) -> RefProtocol | None:
        """Get parent reference in navigation chain.

        Returns:
            Parent ref or None if at root
        """
        ...

    def resolve(self, context: Context) -> PathT:
        """Resolve this reference to a concrete storage path.

        Args:
            context: Execution context

        Returns:
            Path to the location
        """
        ...


# =============================================================================
# PRIMITIVE REF PROTOCOLS
# =============================================================================


@runtime_checkable
class PrimitiveRefProtocol[T, PathT](
    RefProtocol[PathT],
    Gettable[T, object],
    Settable[T, object],
    Deletable[object],
    RefObservable[object],
    Protocol,
):
    """Protocol for primitive (leaf) value references.

    Primitive refs point to single values like int, str, float.
    They support read, write, delete, and observation.

    Type Parameters:
        T: Type of the value at this location
        PathT: Type of the resolved path

    Example:
        >>> if isinstance(ref, PrimitiveRefProtocol):
        ...     get_op = ref.get()
        ...     set_cmd = ref.set(new_value)
        ...     delete_cmd = ref.remove()
    """

    pass


@runtime_checkable
class ValueRefProtocol[T, PathT](
    PrimitiveRefProtocol[T, PathT],
    Protocol,
):
    """Protocol for typed value references.

    Extends PrimitiveRefProtocol with value type information.

    Type Parameters:
        T: Type of the value at this location
        PathT: Type of the resolved path

    Example:
        >>> ref: ValueRefProtocol[int, Path]
        >>> val = ref.get().execute(ctx)  # Returns int
    """

    @property
    def value_type(self) -> type[T]:
        """Get the value type at this location.

        Returns:
            Type of value stored
        """
        ...


# =============================================================================
# VIEW REF PROTOCOLS
# =============================================================================


@runtime_checkable
class ViewRefProtocol[ViewT, PathT](
    RefProtocol[PathT],
    Extractable[object, object],
    Storable[object, object],
    Clearable[object],
    Lengthable[object],
    RefObservable[object],
    RefChildObservable[object, object],
    RefDescendantsObservable[object],
    Protocol,
):
    """Protocol for container (view) references.

    View refs point to container nodes like dict, list, set.
    They support extraction, storage, clearing, and observation.

    Type Parameters:
        ViewT: Type of the view at this location
        PathT: Type of the resolved path

    Example:
        >>> if isinstance(ref, ViewRefProtocol):
        ...     extract_op = ref.extract()
        ...     store_cmd = ref.store(data)
        ...     clear_cmd = ref.clear()
    """

    @property
    def view_type(self) -> type[ViewT]:
        """Get the view type for this container.

        Returns:
            View class
        """
        ...


# =============================================================================
# SEQUENCE REF PROTOCOLS
# =============================================================================


@runtime_checkable
class SequenceRefProtocol[T, PathT](
    ViewRefProtocol[object, PathT],
    RefIndexable[int, object],
    RefSliceable[object],
    Protocol,
):
    """Protocol for read-only sequence references.

    Sequence refs point to list-like containers.
    They support index access, slicing, length, and extraction.

    Type Parameters:
        T: Type of items in the sequence
        PathT: Type of the resolved path

    Example:
        >>> if isinstance(ref, SequenceRefProtocol):
        ...     first = ref[0].get().execute(ctx)
        ...     slice_ref = ref[1:5]
        ...     all_items = ref.extract().execute(ctx)
    """

    @property
    def item_type(self) -> type[T]:
        """Get the item type for this sequence.

        Returns:
            Type of items
        """
        ...


@runtime_checkable
class MutableSequenceRefProtocol[T, PathT](
    SequenceRefProtocol[T, PathT],
    Appendable[T, object],
    Insertable[T, object],
    Poppable[T, object],
    Protocol,
):
    """Protocol for mutable sequence references.

    Extends SequenceRefProtocol with mutation operations.

    Type Parameters:
        T: Type of items in the sequence
        PathT: Type of the resolved path

    Example:
        >>> if isinstance(ref, MutableSequenceRefProtocol):
        ...     append_cmd = ref.append(new_item)
        ...     pop_cmd = ref.pop()
    """

    pass


# =============================================================================
# MAPPING REF PROTOCOLS
# =============================================================================


@runtime_checkable
class MappingRefProtocol[K, V, PathT](
    ViewRefProtocol[object, PathT],
    Nestable[K, object],
    KeysQueryable[object],
    ValuesQueryable[object],
    ItemsQueryable[object],
    Protocol,
):
    """Protocol for read-only mapping references.

    Mapping refs point to dict-like containers.
    They support key access, keys/values/items queries, and extraction.

    Type Parameters:
        K: Type of keys
        V: Type of values
        PathT: Type of the resolved path

    Example:
        >>> if isinstance(ref, MappingRefProtocol):
        ...     item_ref = ref["key"]
        ...     all_keys = ref.keys().execute(ctx)
        ...     all_items = ref.items().execute(ctx)
    """

    @property
    def key_type(self) -> type[K]:
        """Get the key type for this mapping.

        Returns:
            Type of keys
        """
        ...

    @property
    def value_type(self) -> type[V]:
        """Get the value type for this mapping.

        Returns:
            Type of values
        """
        ...


@runtime_checkable
class MutableMappingRefProtocol[K, V, PathT](
    MappingRefProtocol[K, V, PathT],
    Protocol,
):
    """Protocol for mutable mapping references.

    Extends MappingRefProtocol with mutation operations.
    Mutations happen through child refs obtained via __getitem__.

    Type Parameters:
        K: Type of keys
        V: Type of values
        PathT: Type of the resolved path

    Example:
        >>> if isinstance(ref, MutableMappingRefProtocol):
        ...     ref["new_key"].set(value)
        ...     clear_cmd = ref.clear()
    """

    pass


# =============================================================================
# SET REF PROTOCOLS
# =============================================================================


@runtime_checkable
class SetRefProtocol[T, PathT](
    ViewRefProtocol[object, PathT],
    Protocol,
):
    """Protocol for read-only set references.

    Set refs point to set-like containers.
    They support containment checking, length, and extraction.

    Type Parameters:
        T: Type of items in the set
        PathT: Type of the resolved path

    Example:
        >>> if isinstance(ref, SetRefProtocol):
        ...     all_items = ref.extract().execute(ctx)
        ...     size = ref.length().execute(ctx)
    """

    @property
    def item_type(self) -> type[T]:
        """Get the item type for this set.

        Returns:
            Type of items
        """
        ...


@runtime_checkable
class MutableSetRefProtocol[T, PathT](
    SetRefProtocol[T, PathT],
    Protocol,
):
    """Protocol for mutable set references.

    Extends SetRefProtocol with mutation operations.

    Type Parameters:
        T: Type of items in the set
        PathT: Type of the resolved path

    Example:
        >>> if isinstance(ref, MutableSetRefProtocol):
        ...     add_cmd = ref.add(item)
        ...     remove_cmd = ref.remove(item)
    """

    def add(self, value: T) -> object:
        """Create an add command.

        Args:
            value: Item to add

        Returns:
            AddCmd that adds the item when executed
        """
        ...

    def remove(self, value: T) -> object:
        """Create a remove command.

        Args:
            value: Item to remove

        Returns:
            RemoveCmd that removes the item when executed
        """
        ...

    def discard(self, value: T) -> object:
        """Create a discard command.

        Args:
            value: Item to discard (no error if absent)

        Returns:
            DiscardCmd that discards the item when executed
        """
        ...
