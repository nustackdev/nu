"""Core capability implementation bases for LValue references.

This module provides the fundamental capability bases:
- ExistableBase - existence checking (exists(), missing())
- GettableBase - reading values (get()) - for ALL refs
- SettableBase - writing values (set())
- StorableBase - storing container contents (store())
- DeletableBase - deleting values (remove())
- ClearableBase - clearing containers (clear())
- LengthableBase - length queries (length())

Note: .get() is now the unified read method for both primitives and containers.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, overload

from everybase import (
    BoolRef,
    BytesRef,
    DictRef,
    FloatRef,
    IntRef,
    ListRef,
    NoneRef,
    SetRef,
    StrRef,
    ensure_term,
    typed_ref,
)


if TYPE_CHECKING:
    from every import Sentinel, Term


__all__ = [
    "ClearableBase",
    "CollectionGettableBase",
    "DeletableBase",
    "ExistableBase",
    "GettableBase",
    "LengthableBase",
    "SettableBase",
    "StorableBase",
]


# =============================================================================
# EXISTENCE CAPABILITY BASE
# =============================================================================


class ExistableBase:
    """Implementation base for existence checking.

    Implements the Existable protocol with exists() and missing() methods.
    Requires self to have resolve() method.
    """

    def exists(self) -> BoolRef:
        """Create an existence check operation.

        Returns:
            ExistsOp that returns True if location exists

        Example:
            >>> if ref.exists().execute(ctx):
            ...     print("Value exists")
        """
        from every_pv.morphisms import ExistsOp

        return BoolRef(ExistsOp(self))

    def missing(self) -> BoolRef:
        """Create a missing check operation.

        Returns:
            MissingOp that returns True if location doesn't exist

        Example:
            >>> if ref.missing().execute(ctx):
            ...     ref.set(default_value).execute(ctx)
        """
        from every_pv.morphisms import MissingOp

        return BoolRef(MissingOp(self))


# =============================================================================
# READ CAPABILITY BASES
# =============================================================================


class GettableBase[ValueT]:
    """Implementation base for getting primitive values.

    Implements the Gettable protocol with get() method.
    Requires self to have value_type attribute.
    """

    value_type: type[ValueT]

    # Primitives
    @overload
    def get(self: GettableBase[int]) -> IntRef: ...

    @overload
    def get(self: GettableBase[str]) -> StrRef: ...

    @overload
    def get(self: GettableBase[bool]) -> BoolRef: ...

    @overload
    def get(self: GettableBase[float]) -> FloatRef: ...

    @overload
    def get(self: GettableBase[bytes]) -> BytesRef: ...

    @overload
    def get(self: GettableBase[None]) -> NoneRef: ...

    # Collections
    @overload
    def get[V](self: GettableBase[list[V]]) -> ListRef[V]: ...

    @overload
    def get[K, V](self: GettableBase[dict[K, V]]) -> DictRef[K, V]: ...

    @overload
    def get[V](self: GettableBase[set[V]]) -> SetRef[V]: ...

    def get(self) -> object:
        """Create a get operation for this location.

        Returns:
            GetOp that reads the value when executed

        Example:
            >>> value = ref.get().execute(ctx)
        """
        from every_pv.morphisms import GetOp

        return typed_ref(self.value_type, GetOp(self))


class CollectionGettableBase[CollectionTypeT](ABC):
    """Implementation base for getting container contents.

    Implements get() for ViewRefs (containers).
    Unified with GettableBase - all refs now use .get() for reading.
    """

    @abstractmethod
    def result(self, op: Term) -> CollectionTypeT:
        """Wrap an operation result in the appropriate typed container.

        Args:
            op: The operation to wrap

        Returns:
            Typed wrapper (e.g., ListRef, DictRef, SetRef)

        Note:
            Subclasses must implement this to return the correct wrapper type.

        Example:
            def result(self, op: Term) -> ListRef[T]:
                return ListRef(op)
        """
        ...

    def get(self) -> CollectionTypeT:
        """Create a get operation for this container.

        Returns the entire container contents as a typed expression.

        Returns:
            ExtractOp that extracts entire structure when executed

        Example:
            >>> data = dict_ref.get().execute(ctx)  # Returns dict
            >>> items = list_ref.get().execute(ctx)  # Returns list
        """
        from every_pv.morphisms import ExtractOp

        return self.result(ExtractOp(self))


# Backwards compatibility alias
ExtractableBase = CollectionGettableBase


# =============================================================================
# WRITE CAPABILITY BASES
# =============================================================================


class SettableBase[ValueT]:
    """Implementation base for setting primitive values.

    Implements the Settable protocol with set() method.
    Requires self to have value_type attribute.
    """

    value_type: type[ValueT]

    @overload
    def set(
        self: SettableBase[int], value: ValueT | Sentinel | Term[ValueT | Sentinel]
    ) -> IntRef: ...

    @overload
    def set(
        self: SettableBase[str], value: ValueT | Sentinel | Term[ValueT | Sentinel]
    ) -> StrRef: ...

    @overload
    def set(
        self: SettableBase[bool], value: ValueT | Sentinel | Term[ValueT | Sentinel]
    ) -> BoolRef: ...

    @overload
    def set(
        self: SettableBase[float], value: ValueT | Sentinel | Term[ValueT | Sentinel]
    ) -> FloatRef: ...

    @overload
    def set(
        self: SettableBase[bytes], value: ValueT | Sentinel | Term[ValueT | Sentinel]
    ) -> BytesRef: ...

    @overload
    def set(
        self: SettableBase[None], value: ValueT | Sentinel | Term[ValueT | Sentinel]
    ) -> NoneRef: ...

    # Collections
    @overload
    def set[V](
        self: SettableBase[list[V]], value: ValueT | Sentinel | Term[ValueT | Sentinel]
    ) -> ListRef[V]: ...

    @overload
    def set[K, V](
        self: SettableBase[dict[K, V]], value: ValueT | Sentinel | Term[ValueT | Sentinel]
    ) -> DictRef[K, V]: ...

    @overload
    def set[V](
        self: SettableBase[set[V]], value: ValueT | Sentinel | Term[ValueT | Sentinel]
    ) -> SetRef[V]: ...

    def set(self, value: ValueT | Sentinel | Term[ValueT | Sentinel]) -> object:
        """Create a set command for this location.

        Args:
            value: Value to write (literal or Term)

        Returns:
            SetCmd that writes the value when executed

        Example:
            >>> ref.set(42).execute(ctx)
            >>> ref.set(other_ref.get()).execute(ctx)  # Chain refs
        """
        from every_pv.morphisms import SetCmd

        return typed_ref(self.value_type, SetCmd(self, ensure_term(value)))


class StorableBase[CollectionTypeT, CollectionT](ABC):
    """Implementation base for storing container contents.

    Implements the Storable protocol with store() method.
    """

    @abstractmethod
    def result(self, op: Term) -> CollectionTypeT:
        """Wrap an operation result in the appropriate typed container.

        Args:
            op: The operation to wrap

        Returns:
            Typed wrapper (e.g., ListRef, DictRef, SetRef)

        Note:
            Subclasses must implement this to return the correct wrapper type.

        Example:
            def result(self, op: Term) -> DictRef[K, V]:
                return DictRef(op)
        """
        ...

    def store(
        self, value: CollectionT | Sentinel | Term[CollectionT | Sentinel]
    ) -> CollectionTypeT:
        """Create a store command for this container.

        Args:
            value: Value to store (literal or Term)

        Returns:
            StoreCmd that stores the value when executed

        Example:
            >>> dict_ref.store({"key": "value"}).execute(ctx)
        """
        from every_pv.morphisms import StoreCmd

        return self.result(StoreCmd(self, ensure_term(value)))


# =============================================================================
# DELETE CAPABILITY BASES
# =============================================================================


class DeletableBase:
    """Implementation base for deleting values.

    Implements the Deletable protocol with remove() method.
    """

    def remove(self) -> NoneRef:
        """Create a delete command for this location.

        Returns:
            DeleteCmd that removes the value when executed

        Example:
            >>> ref.remove().execute(ctx)
        """
        from every_pv.morphisms import DeleteCmd

        return NoneRef(DeleteCmd(self))


class ClearableBase:
    """Implementation base for clearing containers.

    Implements the Clearable protocol with clear() method.
    """

    def clear(self) -> NoneRef:
        """Create a clear command for this container.

        Returns:
            ClearCmd that clears all items when executed

        Example:
            >>> list_ref.clear().execute(ctx)
        """
        from every_pv.morphisms import ClearCmd

        return NoneRef(ClearCmd(self))


# =============================================================================
# LENGTH CAPABILITY BASE
# =============================================================================


class LengthableBase:
    """Implementation base for length queries.

    Implements the Lengthable protocol with length() method.
    """

    def length(self) -> IntRef:
        """Create a length query operation.

        Returns:
            LengthOp that returns length when executed

        Example:
            >>> count = list_ref.length().execute(ctx)
        """
        from every_pv.morphisms import LengthOp

        return IntRef(LengthOp(self))
