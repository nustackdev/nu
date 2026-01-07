"""Mapping capability bases for LValue references.

This module provides mapping-related capability bases:
- MappingNestableBase - for key-based navigation
- MappingIterableBase - for functional iteration (map_values, filter, reduce, etc.)
- MappingAccessibleBase - for direct container access (get_item, set_item, remove_item)
"""

from __future__ import annotations

from abc import abstractmethod
from typing import TYPE_CHECKING, overload

from ...comps.ref import (
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
    TupleValue,
)
from ...values.conversion import computed, literal


if TYPE_CHECKING:
    from collections.abc import Callable

    from everyshape.types import SpecialValue

    from ...term import RValue


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
    def _create_child_ref(
        self, key: KeyT | SpecialValue | RValue[KeyT | SpecialValue]
    ) -> ChildRefT:
        """Create a reference to a child at the given key.

        Args:
            key: Child key (literal or RValue[KeyT] for computed key)

        Returns:
            Reference to child at the specified key

        Note:
            Subclasses must implement this to return the appropriate ref type.

        Example:
            def _create_child_ref(self, key: KeyT | RValue[KeyT]) -> ChildRef:
                return ChildRef(self, key)
        """
        ...

    def __getitem__(self, key: KeyT | SpecialValue | RValue[KeyT | SpecialValue]) -> ChildRefT:
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

    def map_values[R](self, func: Callable[[ValueT], R]) -> DictValue[KeyT, R]:
        """Map function over mapping values.

        Args:
            func: Function to apply to each value

        Returns:
            DictValue containing transformed dict at execution time

        Example:
            >>> doubled = scores_ref.map_values(lambda x: x * 2).execute(ctx)
        """
        return DictValue(MapValuesOp(self, func))

    def map_items[K2, V2](self, func: Callable[[KeyT, ValueT], tuple[K2, V2]]) -> DictValue[K2, V2]:
        """Map function over mapping items.

        Args:
            func: Function (key, value) -> (new_key, new_value)

        Returns:
            DictValue containing transformed dict at execution time

        Example:
            >>> upper_keys = dict_ref.map_items(lambda k, v: (k.upper(), v)).execute(ctx)
        """
        return DictValue(MapItemsOp(self, func))

    def filter(self, predicate: Callable[[KeyT, ValueT], bool]) -> DictValue[KeyT, ValueT]:
        """Filter mapping items by predicate.

        Args:
            predicate: Function (key, value) -> bool, keep if True

        Returns:
            DictValue containing filtered dict at execution time

        Example:
            >>> high_scores = scores_ref.filter(lambda k, v: v > 100).execute(ctx)
        """
        return DictValue(FilterItemsOp(self, predicate))

    @overload
    def reduce(self, func: Callable[[int, KeyT, ValueT], int], initial: int) -> IntValue: ...

    @overload
    def reduce(self, func: Callable[[str, KeyT, ValueT], str], initial: str) -> StrValue: ...

    @overload
    def reduce(
        self, func: Callable[[float, KeyT, ValueT], float], initial: float
    ) -> FloatValue: ...

    @overload
    def reduce(self, func: Callable[[bool, KeyT, ValueT], bool], initial: bool) -> BoolValue: ...

    @overload
    def reduce[V2](
        self, func: Callable[[list[V2], KeyT, ValueT], list[V2]], initial: list[V2]
    ) -> ListValue[V2]: ...

    @overload
    def reduce[K2, V2](
        self, func: Callable[[dict[K2, V2], KeyT, ValueT], dict[K2, V2]], initial: dict[K2, V2]
    ) -> DictValue[K2, V2]: ...

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
    ) -> IntValue: ...

    @overload
    def find_key(
        self: MappingIterableBase[str, ValueT], predicate: Callable[[ValueT], bool]
    ) -> StrValue: ...

    @overload
    def find_key(
        self: MappingIterableBase[float, ValueT], predicate: Callable[[ValueT], bool]
    ) -> FloatValue: ...

    @overload
    def find_key(
        self: MappingIterableBase[bool, ValueT], predicate: Callable[[ValueT], bool]
    ) -> BoolValue: ...

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
    ) -> IntValue: ...

    @overload
    def find_value(
        self: MappingIterableBase[KeyT, str], predicate: Callable[[str], bool]
    ) -> StrValue: ...

    @overload
    def find_value(
        self: MappingIterableBase[KeyT, float], predicate: Callable[[float], bool]
    ) -> FloatValue: ...

    @overload
    def find_value(
        self: MappingIterableBase[KeyT, bool], predicate: Callable[[bool], bool]
    ) -> BoolValue: ...

    @overload
    def find_value[V2](
        self: MappingIterableBase[KeyT, list[V2]], predicate: Callable[[list[V2]], bool]
    ) -> ListValue[V2]: ...

    @overload
    def find_value[K2, V2](
        self: MappingIterableBase[KeyT, dict[K2, V2]],
        predicate: Callable[[dict[K2, V2]], bool],
    ) -> DictValue[K2, V2]: ...

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

    def find_item(self, predicate: Callable[[KeyT, ValueT], bool]) -> TupleValue[KeyT, ValueT]:
        """Find first item (key, value) matching predicate.

        Args:
            predicate: Function (key, value) -> bool

        Returns:
            TupleValue containing matching (key, value) tuple at execution time

        Example:
            >>> item = dict_ref.find_item(lambda k, v: k.startswith("admin")).execute(ctx)
        """
        return TupleValue(FindItemByPredicateOp(self, predicate))


class MappingAccessibleBase[KeyT, ValueT]:
    """Implementation base for direct mapping container access.

    Provides get(), set_item(), and remove_item() methods for accessing
    mapping containers directly (without navigating to child refs).
    """

    value_type: type[ValueT]

    @overload
    def get_item(
        self: MappingAccessibleBase[KeyT, int],
        key: KeyT | SpecialValue | RValue[KeyT | SpecialValue],
        default: int | SpecialValue | None = None,
    ) -> IntValue: ...

    @overload
    def get_item(
        self: MappingAccessibleBase[KeyT, str],
        key: KeyT | SpecialValue | RValue[KeyT | SpecialValue],
        default: str | SpecialValue | None = None,
    ) -> StrValue: ...

    @overload
    def get_item(
        self: MappingAccessibleBase[KeyT, bool],
        key: KeyT | SpecialValue | RValue[KeyT | SpecialValue],
        default: bool | SpecialValue | None = None,
    ) -> BoolValue: ...

    @overload
    def get_item(
        self: MappingAccessibleBase[KeyT, float],
        key: KeyT | SpecialValue | RValue[KeyT | SpecialValue],
        default: float | SpecialValue | None = None,
    ) -> FloatValue: ...

    @overload
    def get_item(
        self: MappingAccessibleBase[KeyT, bytes],
        key: KeyT | SpecialValue | RValue[KeyT | SpecialValue],
        default: bytes | SpecialValue | None = None,
    ) -> BytesValue: ...

    @overload
    def get_item(
        self: MappingAccessibleBase[KeyT, None],
        key: KeyT | SpecialValue | RValue[KeyT | SpecialValue],
        default: None | SpecialValue = None,
    ) -> NoneValue: ...

    @overload
    def get_item[V](
        self: MappingAccessibleBase[KeyT, list[V]],
        key: KeyT | SpecialValue | RValue[KeyT | SpecialValue],
        default: list[V] | SpecialValue | None = None,
    ) -> ListValue[V]: ...

    @overload
    def get_item[K, V](
        self: MappingAccessibleBase[KeyT, dict[K, V]],
        key: KeyT | SpecialValue | RValue[KeyT | SpecialValue],
        default: dict[K, V] | SpecialValue | None = None,
    ) -> DictValue[K, V]: ...

    @overload
    def get_item[V](
        self: MappingAccessibleBase[KeyT, set[V]],
        key: KeyT | SpecialValue | RValue[KeyT | SpecialValue],
        default: set[V] | SpecialValue | None = None,
    ) -> SetValue[V]: ...

    def get_item(
        self,
        key: KeyT | SpecialValue | RValue[KeyT | SpecialValue],
        default: ValueT | SpecialValue | None = None,
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
        key: KeyT | SpecialValue | RValue[KeyT | SpecialValue],
        value: int | SpecialValue | RValue[int | SpecialValue],
    ) -> IntValue: ...

    @overload
    def set_item(
        self: MappingAccessibleBase[KeyT, str],
        key: KeyT | SpecialValue | RValue[KeyT | SpecialValue],
        value: str | SpecialValue | RValue[str | SpecialValue],
    ) -> StrValue: ...

    @overload
    def set_item(
        self: MappingAccessibleBase[KeyT, bool],
        key: KeyT | SpecialValue | RValue[KeyT | SpecialValue],
        value: bool | SpecialValue | RValue[bool | SpecialValue],
    ) -> BoolValue: ...

    @overload
    def set_item(
        self: MappingAccessibleBase[KeyT, float],
        key: KeyT | SpecialValue | RValue[KeyT | SpecialValue],
        value: float | SpecialValue | RValue[float | SpecialValue],
    ) -> FloatValue: ...

    @overload
    def set_item(
        self: MappingAccessibleBase[KeyT, bytes],
        key: KeyT | SpecialValue | RValue[KeyT | SpecialValue],
        value: bytes | SpecialValue | RValue[bytes | SpecialValue],
    ) -> BytesValue: ...

    @overload
    def set_item(
        self: MappingAccessibleBase[KeyT, None],
        key: KeyT | SpecialValue | RValue[KeyT | SpecialValue],
        value: None | SpecialValue | RValue[None | SpecialValue],
    ) -> NoneValue: ...

    @overload
    def set_item[V](
        self: MappingAccessibleBase[KeyT, list[V]],
        key: KeyT | SpecialValue | RValue[KeyT | SpecialValue],
        value: list[V] | SpecialValue | RValue[list[V] | SpecialValue],
    ) -> ListValue[V]: ...

    @overload
    def set_item[K, V](
        self: MappingAccessibleBase[KeyT, dict[K, V]],
        key: KeyT | SpecialValue | RValue[KeyT | SpecialValue],
        value: dict[K, V] | SpecialValue | RValue[dict[K, V] | SpecialValue],
    ) -> DictValue[K, V]: ...

    @overload
    def set_item[V](
        self: MappingAccessibleBase[KeyT, set[V]],
        key: KeyT | SpecialValue | RValue[KeyT | SpecialValue],
        value: set[V] | SpecialValue | RValue[set[V] | SpecialValue],
    ) -> SetValue[V]: ...

    def set_item(
        self,
        key: KeyT | SpecialValue | RValue[KeyT | SpecialValue],
        value: ValueT | SpecialValue | RValue[ValueT | SpecialValue],
    ) -> object:
        """Set value at key in mapping.

        Args:
            key: Key to set
            value: Value to set (literal or RValue)

        Returns:
            Typed value wrapper containing the set value

        Example:
            >>> dict_ref.set_item("key", "value").execute(ctx)
        """
        return computed(self.value_type, SetByKeyCmd(self, key, literal(value)))

    def remove_item(self, key: KeyT | SpecialValue | RValue[KeyT | SpecialValue]) -> NoneValue:
        """Remove key from mapping.

        Args:
            key: Key to remove

        Returns:
            NoneValue (remove returns None after execution)

        Note:
            Raises KeyError at execution if key not found.

        Example:
            >>> dict_ref.remove_item("key").execute(ctx)
        """
        return NoneValue(RemoveByKeyCmd(self, key))
