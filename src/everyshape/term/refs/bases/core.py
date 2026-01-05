"""Core capability implementation bases for LValue references.

This module provides the fundamental capability bases:
- ExistableBase - existence checking (exists(), missing())
- GettableBase - reading values (get())
- ExtractableBase - extracting container contents (extract())
- SettableBase - writing values (set())
- StorableBase - storing container contents (store())
- DeletableBase - deleting values (remove())
- ClearableBase - clearing containers (clear())
- LengthableBase - length queries (length())
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, overload

from ...comps import (
    ClearCmd,
    DeleteCmd,
    ExistsOp,
    ExtractOp,
    GetOp,
    LengthOp,
    MissingOp,
    SetCmd,
    StoreCmd,
)
from ...values import (
    BoolValue,
    BytesValue,
    DictValue,
    FloatValue,
    IntValue,
    ListValue,
    NoneValue,
    SetValue,
    StrValue,
)
from ...values.conversion import computed, literal


if TYPE_CHECKING:
    from everyshape.types import SpecialValue

    from ...term import RValue


__all__ = [
    "ClearableBase",
    "DeletableBase",
    "ExistableBase",
    "ExtractableBase",
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

    def exists(self) -> BoolValue:
        """Create an existence check operation.

        Returns:
            ExistsOp that returns True if location exists

        Example:
            >>> if ref.exists().execute(ctx):
            ...     print("Value exists")
        """
        return BoolValue(ExistsOp(self))

    def missing(self) -> BoolValue:
        """Create a missing check operation.

        Returns:
            MissingOp that returns True if location doesn't exist

        Example:
            >>> if ref.missing().execute(ctx):
            ...     ref.set(default_value).execute(ctx)
        """
        return BoolValue(MissingOp(self))


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
    def get(self: GettableBase[int]) -> IntValue: ...

    @overload
    def get(self: GettableBase[str]) -> StrValue: ...

    @overload
    def get(self: GettableBase[bool]) -> BoolValue: ...

    @overload
    def get(self: GettableBase[float]) -> FloatValue: ...

    @overload
    def get(self: GettableBase[bytes]) -> BytesValue: ...

    @overload
    def get(self: GettableBase[None]) -> NoneValue: ...

    # Collections
    @overload
    def get[V](self: GettableBase[list[V]]) -> ListValue[V]: ...

    @overload
    def get[K, V](self: GettableBase[dict[K, V]]) -> DictValue[K, V]: ...

    @overload
    def get[V](self: GettableBase[set[V]]) -> SetValue[V]: ...

    def get(self) -> object:
        """Create a get operation for this location.

        Returns:
            GetOp that reads the value when executed

        Example:
            >>> value = ref.get().execute(ctx)
        """
        return computed(self.value_type, GetOp(self))


class ExtractableBase[CollectionValueT](ABC):
    """Implementation base for extracting container contents.

    Implements the Extractable protocol with extract() method.
    """

    @abstractmethod
    def result(self, op: RValue) -> CollectionValueT:
        """Wrap an operation result in the appropriate typed value container.

        Args:
            op: The operation to wrap

        Returns:
            Typed value wrapper (e.g., ListValue, DictValue, SetValue)

        Note:
            Subclasses must implement this to return the correct wrapper type.

        Example:
            def result(self, op: RValue) -> ListValue[T]:
                return ListValue(op)
        """
        ...

    def extract(self) -> CollectionValueT:
        """Create an extract operation for this container.

        Returns:
            ExtractOp that extracts entire structure when executed

        Example:
            >>> data = dict_ref.extract().execute(ctx)  # Returns dict
        """
        return self.result(ExtractOp(self))


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
        self: SettableBase[int], value: ValueT | SpecialValue | RValue[ValueT | SpecialValue]
    ) -> IntValue: ...

    @overload
    def set(
        self: SettableBase[str], value: ValueT | SpecialValue | RValue[ValueT | SpecialValue]
    ) -> StrValue: ...

    @overload
    def set(
        self: SettableBase[bool], value: ValueT | SpecialValue | RValue[ValueT | SpecialValue]
    ) -> BoolValue: ...

    @overload
    def set(
        self: SettableBase[float], value: ValueT | SpecialValue | RValue[ValueT | SpecialValue]
    ) -> FloatValue: ...

    @overload
    def set(
        self: SettableBase[bytes], value: ValueT | SpecialValue | RValue[ValueT | SpecialValue]
    ) -> BytesValue: ...

    @overload
    def set(
        self: SettableBase[None], value: ValueT | SpecialValue | RValue[ValueT | SpecialValue]
    ) -> NoneValue: ...

    # Collections
    @overload
    def set[V](
        self: SettableBase[list[V]], value: ValueT | SpecialValue | RValue[ValueT | SpecialValue]
    ) -> ListValue[V]: ...

    @overload
    def set[K, V](
        self: SettableBase[dict[K, V]], value: ValueT | SpecialValue | RValue[ValueT | SpecialValue]
    ) -> DictValue[K, V]: ...

    @overload
    def set[V](
        self: SettableBase[set[V]], value: ValueT | SpecialValue | RValue[ValueT | SpecialValue]
    ) -> SetValue[V]: ...

    def set(self, value: ValueT | SpecialValue | RValue[ValueT | SpecialValue]) -> object:
        """Create a set command for this location.

        Args:
            value: Value to write (literal or RValue)

        Returns:
            SetCmd that writes the value when executed

        Example:
            >>> ref.set(42).execute(ctx)
            >>> ref.set(other_ref.get()).execute(ctx)  # Chain refs
        """
        return computed(self.value_type, SetCmd(self, literal(value)))


class StorableBase[CollectionValueT, CollectionT](ABC):
    """Implementation base for storing container contents.

    Implements the Storable protocol with store() method.
    """

    @abstractmethod
    def result(self, op: RValue) -> CollectionValueT:
        """Wrap an operation result in the appropriate typed value container.

        Args:
            op: The operation to wrap

        Returns:
            Typed value wrapper (e.g., ListValue, DictValue, SetValue)

        Note:
            Subclasses must implement this to return the correct wrapper type.

        Example:
            def result(self, op: RValue) -> DictValue[K, V]:
                return DictValue(op)
        """
        ...

    def store(
        self, value: CollectionT | SpecialValue | RValue[CollectionT | SpecialValue]
    ) -> CollectionValueT:
        """Create a store command for this container.

        Args:
            value: Value to store (literal or RValue)

        Returns:
            StoreCmd that stores the value when executed

        Example:
            >>> dict_ref.store({"key": "value"}).execute(ctx)
        """
        return self.result(StoreCmd(self, literal(value)))


# =============================================================================
# DELETE CAPABILITY BASES
# =============================================================================


class DeletableBase:
    """Implementation base for deleting values.

    Implements the Deletable protocol with remove() method.
    """

    def remove(self) -> NoneValue:
        """Create a delete command for this location.

        Returns:
            DeleteCmd that removes the value when executed

        Example:
            >>> ref.remove().execute(ctx)
        """
        return NoneValue(DeleteCmd(self))


class ClearableBase:
    """Implementation base for clearing containers.

    Implements the Clearable protocol with clear() method.
    """

    def clear(self) -> NoneValue:
        """Create a clear command for this container.

        Returns:
            ClearCmd that clears all items when executed

        Example:
            >>> list_ref.clear().execute(ctx)
        """
        return NoneValue(ClearCmd(self))


# =============================================================================
# LENGTH CAPABILITY BASE
# =============================================================================


class LengthableBase:
    """Implementation base for length queries.

    Implements the Lengthable protocol with length() method.
    """

    def length(self) -> IntValue:
        """Create a length query operation.

        Returns:
            LengthOp that returns length when executed

        Example:
            >>> count = list_ref.length().execute(ctx)
        """
        return IntValue(LengthOp(self))
