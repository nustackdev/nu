"""Mapping capability bases for LValue references.

This module provides mapping-related capability bases:
- MappingNestableBase - for key-based navigation
- MappingIterableBase - for functional iteration (map_values, filter, reduce, etc.)
- MappingAccessibleBase - for direct container access (get_item, set_item, remove_item)
"""

from __future__ import annotations

from abc import abstractmethod
from typing import TYPE_CHECKING, overload

from everyterm.term import Term, computed, literal
from everyterm.types import DictType, NoneType, TupleType

from ..comp import (
    FilterItemsOp,
    FindItemByPredicateOp,
    FindKeyByPredicateOp,
    FindValueByPredicateOp,
    GetByKeyOp,
    MapItemsOp,
    MapValuesOp,
    ReduceItemsOp,
    RemoveByKeyCmd,
    SetByKeyCmd,
)


if TYPE_CHECKING:
    from collections.abc import Callable

    from everyterm.term import Term
    from everyterm.types import BoolType, BytesType, FloatType, IntType, ListType, SetType, StrType
    from everyterm.typing import Sentinel


__all__ = [
    "MappingAccessibleBase",
    "MappingIterableBase",
    "MappingNestableBase",
]


# =============================================================================
# MAPPING CAPABILITY BASES
# =============================================================================


class MappingNestableBase[KeyT, ChildRefT]:
    """Implementation base for mapping navigation.

    Provides __getitem__ for key-based child access.
    Subclasses must implement _create_child_ref.
    """

    @abstractmethod
    def _create_child_ref(self, key: KeyT | Sentinel | Term[KeyT | Sentinel]) -> ChildRefT:
        """Create a reference to a child at the given key.

        Args:
            key: Child key (literal or Term[KeyT] for computed key)

        Returns:
            Reference to child at the specified key

        Note:
            Subclasses must implement this to return the appropriate ref type.

        Example:
            def _create_child_ref(self, key: KeyT | Term[KeyT]) -> ChildRef:
                return ChildRef(self, key)
        """
        ...

    def __getitem__(self, key: KeyT | Sentinel | Term[KeyT | Sentinel]) -> ChildRefT:
        """Get child reference by key.

        Args:
            key: Key value

        Returns:
            Reference to item at key

        Example:
            >>> user_ref = users_ref["alice"]
        """
        return self._create_child_ref(key)


class MappingIterableBase[KeyT, ValueT]:
    """Implementation base for mapping iteration operations.

    Provides map_values(), map_items(), filter(), reduce(),
    find_key(), find_value(), find_item().
    Requires self to have key_type and value_type attributes.
    """

    key_type: type[KeyT]
    value_type: type[ValueT]

    def map_values[R](self, func: Callable[[ValueT], R]) -> DictType[KeyT, R]:
        """Map function over mapping values.

        Args:
            func: Function to apply to each value

        Returns:
            DictType containing transformed dict at execution time

        Example:
            >>> doubled = scores_ref.map_values(lambda x: x * 2).execute(ctx)
        """
        return DictType(MapValuesOp(self, func))

    def map_items[K2, V2](self, func: Callable[[KeyT, ValueT], tuple[K2, V2]]) -> DictType[K2, V2]:
        """Map function over mapping items.

        Args:
            func: Function (key, value) -> (new_key, new_value)

        Returns:
            DictType containing transformed dict at execution time

        Example:
            >>> upper_keys = dict_ref.map_items(lambda k, v: (k.upper(), v)).execute(ctx)
        """
        return DictType(MapItemsOp(self, func))

    def filter(self, predicate: Callable[[KeyT, ValueT], bool]) -> DictType[KeyT, ValueT]:
        """Filter mapping items by predicate.

        Args:
            predicate: Function (key, value) -> bool, keep if True

        Returns:
            DictType containing filtered dict at execution time

        Example:
            >>> high_scores = scores_ref.filter(lambda k, v: v > 100).execute(ctx)
        """
        return DictType(FilterItemsOp(self, predicate))

    @overload
    def reduce(self, func: Callable[[int, KeyT, ValueT], int], initial: int) -> IntType: ...

    @overload
    def reduce(self, func: Callable[[str, KeyT, ValueT], str], initial: str) -> StrType: ...

    @overload
    def reduce(self, func: Callable[[float, KeyT, ValueT], float], initial: float) -> FloatType: ...

    @overload
    def reduce(self, func: Callable[[bool, KeyT, ValueT], bool], initial: bool) -> BoolType: ...

    @overload
    def reduce[V2](
        self, func: Callable[[list[V2], KeyT, ValueT], list[V2]], initial: list[V2]
    ) -> ListType[V2]: ...

    @overload
    def reduce[K2, V2](
        self, func: Callable[[dict[K2, V2], KeyT, ValueT], dict[K2, V2]], initial: dict[K2, V2]
    ) -> DictType[K2, V2]: ...

    def reduce[R](self, func: Callable[[R, KeyT, ValueT], R], initial: R) -> object:
        """Reduce mapping to single value.

        Args:
            func: Function (accumulator, key, value) -> new_accumulator
            initial: Starting value for accumulator

        Returns:
            Typed value wrapper containing reduced value at execution time

        Example:
            >>> total = scores_ref.reduce(lambda acc, k, v: acc + v, 0).execute(ctx)
        """
        return computed(type(initial), ReduceItemsOp(self, func, initial))

    @overload
    def find_key(
        self: MappingIterableBase[int, ValueT], predicate: Callable[[ValueT], bool]
    ) -> IntType: ...

    @overload
    def find_key(
        self: MappingIterableBase[str, ValueT], predicate: Callable[[ValueT], bool]
    ) -> StrType: ...

    @overload
    def find_key(
        self: MappingIterableBase[float, ValueT], predicate: Callable[[ValueT], bool]
    ) -> FloatType: ...

    @overload
    def find_key(
        self: MappingIterableBase[bool, ValueT], predicate: Callable[[ValueT], bool]
    ) -> BoolType: ...

    def find_key(self, predicate: Callable[[ValueT], bool]) -> object:
        """Find first key whose value matches predicate.

        Args:
            predicate: Function applied to values, return True to match

        Returns:
            Typed value wrapper containing matching key at execution time

        Example:
            >>> winner = scores_ref.find_key(lambda v: v >= 100).execute(ctx)
        """
        return computed(self.key_type, FindKeyByPredicateOp(self, predicate))

    @overload
    def find_value(
        self: MappingIterableBase[KeyT, int], predicate: Callable[[int], bool]
    ) -> IntType: ...

    @overload
    def find_value(
        self: MappingIterableBase[KeyT, str], predicate: Callable[[str], bool]
    ) -> StrType: ...

    @overload
    def find_value(
        self: MappingIterableBase[KeyT, float], predicate: Callable[[float], bool]
    ) -> FloatType: ...

    @overload
    def find_value(
        self: MappingIterableBase[KeyT, bool], predicate: Callable[[bool], bool]
    ) -> BoolType: ...

    @overload
    def find_value[V2](
        self: MappingIterableBase[KeyT, list[V2]], predicate: Callable[[list[V2]], bool]
    ) -> ListType[V2]: ...

    @overload
    def find_value[K2, V2](
        self: MappingIterableBase[KeyT, dict[K2, V2]],
        predicate: Callable[[dict[K2, V2]], bool],
    ) -> DictType[K2, V2]: ...

    def find_value(self, predicate: Callable) -> object:
        """Find first value matching predicate.

        Args:
            predicate: Function applied to values, return True to match

        Returns:
            Typed value wrapper containing matching value at execution time

        Example:
            >>> high_score = scores_ref.find_value(lambda v: v >= 100).execute(ctx)
        """
        return computed(self.value_type, FindValueByPredicateOp(self, predicate))

    def find_item(self, predicate: Callable[[KeyT, ValueT], bool]) -> TupleType[KeyT, ValueT]:
        """Find first item (key, value) matching predicate.

        Args:
            predicate: Function (key, value) -> bool

        Returns:
            TupleType containing matching (key, value) tuple at execution time

        Example:
            >>> item = dict_ref.find_item(lambda k, v: k.startswith("admin")).execute(ctx)
        """
        return TupleType(FindItemByPredicateOp(self, predicate))


class MappingAccessibleBase[KeyT, ValueT]:
    """Implementation base for direct mapping container access.

    Provides get(), set_item(), and remove_item() methods for accessing
    mapping containers directly (without navigating to child refs).
    """

    value_type: type[ValueT]

    @overload
    def get_item(
        self: MappingAccessibleBase[KeyT, int],
        key: KeyT | Sentinel | Term[KeyT | Sentinel],
        default: int | Sentinel | None = None,
    ) -> IntType: ...

    @overload
    def get_item(
        self: MappingAccessibleBase[KeyT, str],
        key: KeyT | Sentinel | Term[KeyT | Sentinel],
        default: str | Sentinel | None = None,
    ) -> StrType: ...

    @overload
    def get_item(
        self: MappingAccessibleBase[KeyT, bool],
        key: KeyT | Sentinel | Term[KeyT | Sentinel],
        default: bool | Sentinel | None = None,
    ) -> BoolType: ...

    @overload
    def get_item(
        self: MappingAccessibleBase[KeyT, float],
        key: KeyT | Sentinel | Term[KeyT | Sentinel],
        default: float | Sentinel | None = None,
    ) -> FloatType: ...

    @overload
    def get_item(
        self: MappingAccessibleBase[KeyT, bytes],
        key: KeyT | Sentinel | Term[KeyT | Sentinel],
        default: bytes | Sentinel | None = None,
    ) -> BytesType: ...

    @overload
    def get_item(
        self: MappingAccessibleBase[KeyT, None],
        key: KeyT | Sentinel | Term[KeyT | Sentinel],
        default: None | Sentinel = None,
    ) -> NoneType: ...

    @overload
    def get_item[V](
        self: MappingAccessibleBase[KeyT, list[V]],
        key: KeyT | Sentinel | Term[KeyT | Sentinel],
        default: list[V] | Sentinel | None = None,
    ) -> ListType[V]: ...

    @overload
    def get_item[K, V](
        self: MappingAccessibleBase[KeyT, dict[K, V]],
        key: KeyT | Sentinel | Term[KeyT | Sentinel],
        default: dict[K, V] | Sentinel | None = None,
    ) -> DictType[K, V]: ...

    @overload
    def get_item[V](
        self: MappingAccessibleBase[KeyT, set[V]],
        key: KeyT | Sentinel | Term[KeyT | Sentinel],
        default: set[V] | Sentinel | None = None,
    ) -> SetType[V]: ...

    def get_item(
        self,
        key: KeyT | Sentinel | Term[KeyT | Sentinel],
        default: ValueT | Sentinel | None = None,
    ) -> object:
        """Get value by key with optional default.

        Args:
            key: Key to look up
            default: Value to return if key not found (default: Empty)

        Returns:
            Typed value wrapper containing value at key or default

        Example:
            >>> value = dict_ref.get_item("key", "default").execute(ctx)
        """
        return computed(self.value_type, GetByKeyOp(self, key, default))

    @overload
    def set_item(
        self: MappingAccessibleBase[KeyT, int],
        key: KeyT | Sentinel | Term[KeyT | Sentinel],
        value: int | Sentinel | Term[int | Sentinel],
    ) -> IntType: ...

    @overload
    def set_item(
        self: MappingAccessibleBase[KeyT, str],
        key: KeyT | Sentinel | Term[KeyT | Sentinel],
        value: str | Sentinel | Term[str | Sentinel],
    ) -> StrType: ...

    @overload
    def set_item(
        self: MappingAccessibleBase[KeyT, bool],
        key: KeyT | Sentinel | Term[KeyT | Sentinel],
        value: bool | Sentinel | Term[bool | Sentinel],
    ) -> BoolType: ...

    @overload
    def set_item(
        self: MappingAccessibleBase[KeyT, float],
        key: KeyT | Sentinel | Term[KeyT | Sentinel],
        value: float | Sentinel | Term[float | Sentinel],
    ) -> FloatType: ...

    @overload
    def set_item(
        self: MappingAccessibleBase[KeyT, bytes],
        key: KeyT | Sentinel | Term[KeyT | Sentinel],
        value: bytes | Sentinel | Term[bytes | Sentinel],
    ) -> BytesType: ...

    @overload
    def set_item(
        self: MappingAccessibleBase[KeyT, None],
        key: KeyT | Sentinel | Term[KeyT | Sentinel],
        value: None | Sentinel | Term[None | Sentinel],
    ) -> NoneType: ...

    @overload
    def set_item[V](
        self: MappingAccessibleBase[KeyT, list[V]],
        key: KeyT | Sentinel | Term[KeyT | Sentinel],
        value: list[V] | Sentinel | Term[list[V] | Sentinel],
    ) -> ListType[V]: ...

    @overload
    def set_item[K, V](
        self: MappingAccessibleBase[KeyT, dict[K, V]],
        key: KeyT | Sentinel | Term[KeyT | Sentinel],
        value: dict[K, V] | Sentinel | Term[dict[K, V] | Sentinel],
    ) -> DictType[K, V]: ...

    @overload
    def set_item[V](
        self: MappingAccessibleBase[KeyT, set[V]],
        key: KeyT | Sentinel | Term[KeyT | Sentinel],
        value: set[V] | Sentinel | Term[set[V] | Sentinel],
    ) -> SetType[V]: ...

    def set_item(
        self,
        key: KeyT | Sentinel | Term[KeyT | Sentinel],
        value: ValueT | Sentinel | Term[ValueT | Sentinel],
    ) -> object:
        """Set value at key in mapping.

        Args:
            key: Key to set
            value: Value to set (literal or Term)

        Returns:
            Typed value wrapper containing the set value

        Example:
            >>> dict_ref.set_item("key", "value").execute(ctx)
        """
        return computed(self.value_type, SetByKeyCmd(self, key, literal(value)))

    def remove_item(self, key: KeyT | Sentinel | Term[KeyT | Sentinel]) -> NoneType:
        """Remove key from mapping.

        Args:
            key: Key to remove

        Returns:
            NoneType (remove returns None after execution)

        Note:
            Raises KeyError at execution if key not found.

        Example:
            >>> dict_ref.remove_item("key").execute(ctx)
        """
        return NoneType(RemoveByKeyCmd(self, key))
