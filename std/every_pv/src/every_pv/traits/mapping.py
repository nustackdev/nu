"""Mapping capability bases for LValue references.

This module provides mapping-related capability bases:
- MappingNestableBase - for key-based navigation
- MappingIterableBase - for functional iteration (map_values, filter, reduce, etc.)
- MappingAccessibleBase - for direct container access (get_item, set_item, remove_item)
"""

from __future__ import annotations

from abc import abstractmethod
from typing import TYPE_CHECKING, overload

from everyabc import Term
from everybase import DictRef, NoneRef, TupleRef, ensure_term, typed_ref


if TYPE_CHECKING:
    from collections.abc import Callable

    from everyabc import Sentinel, Term
    from everybase import BoolRef, BytesRef, FloatRef, IntRef, ListRef, SetRef, StrRef


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

    def map_values[R](self, func: Callable[[ValueT], R]) -> DictRef[KeyT, R]:
        """Map function over mapping values.

        Args:
            func: Function to apply to each value

        Returns:
            DictRef containing transformed dict at execution time

        Example:
            >>> doubled = scores_ref.map_values(lambda x: x * 2).execute(ctx)
        """
        from every_pv.morphisms import MapValuesOp

        return DictRef(MapValuesOp(self, func))

    def map_items[K2, V2](self, func: Callable[[KeyT, ValueT], tuple[K2, V2]]) -> DictRef[K2, V2]:
        """Map function over mapping items.

        Args:
            func: Function (key, value) -> (new_key, new_value)

        Returns:
            DictRef containing transformed dict at execution time

        Example:
            >>> upper_keys = dict_ref.map_items(lambda k, v: (k.upper(), v)).execute(ctx)
        """
        from every_pv.morphisms import MapItemsOp

        return DictRef(MapItemsOp(self, func))

    def filter(self, predicate: Callable[[KeyT, ValueT], bool]) -> DictRef[KeyT, ValueT]:
        """Filter mapping items by predicate.

        Args:
            predicate: Function (key, value) -> bool, keep if True

        Returns:
            DictRef containing filtered dict at execution time

        Example:
            >>> high_scores = scores_ref.filter(lambda k, v: v > 100).execute(ctx)
        """
        from every_pv.morphisms import FilterItemsOp

        return DictRef(FilterItemsOp(self, predicate))

    @overload
    def reduce(self, func: Callable[[int, KeyT, ValueT], int], initial: int) -> IntRef: ...

    @overload
    def reduce(self, func: Callable[[str, KeyT, ValueT], str], initial: str) -> StrRef: ...

    @overload
    def reduce(self, func: Callable[[float, KeyT, ValueT], float], initial: float) -> FloatRef: ...

    @overload
    def reduce(self, func: Callable[[bool, KeyT, ValueT], bool], initial: bool) -> BoolRef: ...

    @overload
    def reduce[V2](
        self, func: Callable[[list[V2], KeyT, ValueT], list[V2]], initial: list[V2]
    ) -> ListRef[V2]: ...

    @overload
    def reduce[K2, V2](
        self, func: Callable[[dict[K2, V2], KeyT, ValueT], dict[K2, V2]], initial: dict[K2, V2]
    ) -> DictRef[K2, V2]: ...

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
        from every_pv.morphisms import ReduceItemsOp

        return typed_ref(type(initial), ReduceItemsOp(self, func, initial))

    @overload
    def find_key(
        self: MappingIterableBase[int, ValueT], predicate: Callable[[ValueT], bool]
    ) -> IntRef: ...

    @overload
    def find_key(
        self: MappingIterableBase[str, ValueT], predicate: Callable[[ValueT], bool]
    ) -> StrRef: ...

    @overload
    def find_key(
        self: MappingIterableBase[float, ValueT], predicate: Callable[[ValueT], bool]
    ) -> FloatRef: ...

    @overload
    def find_key(
        self: MappingIterableBase[bool, ValueT], predicate: Callable[[ValueT], bool]
    ) -> BoolRef: ...

    def find_key(self, predicate: Callable[[ValueT], bool]) -> object:
        """Find first key whose value matches predicate.

        Args:
            predicate: Function applied to values, return True to match

        Returns:
            Typed value wrapper containing matching key at execution time

        Example:
            >>> winner = scores_ref.find_key(lambda v: v >= 100).execute(ctx)
        """
        from every_pv.morphisms import FindKeyByPredicateOp

        return typed_ref(self.key_type, FindKeyByPredicateOp(self, predicate))

    @overload
    def find_value(
        self: MappingIterableBase[KeyT, int], predicate: Callable[[int], bool]
    ) -> IntRef: ...

    @overload
    def find_value(
        self: MappingIterableBase[KeyT, str], predicate: Callable[[str], bool]
    ) -> StrRef: ...

    @overload
    def find_value(
        self: MappingIterableBase[KeyT, float], predicate: Callable[[float], bool]
    ) -> FloatRef: ...

    @overload
    def find_value(
        self: MappingIterableBase[KeyT, bool], predicate: Callable[[bool], bool]
    ) -> BoolRef: ...

    @overload
    def find_value[V2](
        self: MappingIterableBase[KeyT, list[V2]], predicate: Callable[[list[V2]], bool]
    ) -> ListRef[V2]: ...

    @overload
    def find_value[K2, V2](
        self: MappingIterableBase[KeyT, dict[K2, V2]],
        predicate: Callable[[dict[K2, V2]], bool],
    ) -> DictRef[K2, V2]: ...

    def find_value(self, predicate: Callable) -> object:
        """Find first value matching predicate.

        Args:
            predicate: Function applied to values, return True to match

        Returns:
            Typed value wrapper containing matching value at execution time

        Example:
            >>> high_score = scores_ref.find_value(lambda v: v >= 100).execute(ctx)
        """
        from every_pv.morphisms import FindValueByPredicateOp

        return typed_ref(self.value_type, FindValueByPredicateOp(self, predicate))

    def find_item(self, predicate: Callable[[KeyT, ValueT], bool]) -> TupleRef[KeyT, ValueT]:
        """Find first item (key, value) matching predicate.

        Args:
            predicate: Function (key, value) -> bool

        Returns:
            TupleRef containing matching (key, value) tuple at execution time

        Example:
            >>> item = dict_ref.find_item(lambda k, v: k.startswith("admin")).execute(ctx)
        """
        from every_pv.morphisms import FindItemByPredicateOp

        return TupleRef(FindItemByPredicateOp(self, predicate))


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
    ) -> IntRef: ...

    @overload
    def get_item(
        self: MappingAccessibleBase[KeyT, str],
        key: KeyT | Sentinel | Term[KeyT | Sentinel],
        default: str | Sentinel | None = None,
    ) -> StrRef: ...

    @overload
    def get_item(
        self: MappingAccessibleBase[KeyT, bool],
        key: KeyT | Sentinel | Term[KeyT | Sentinel],
        default: bool | Sentinel | None = None,
    ) -> BoolRef: ...

    @overload
    def get_item(
        self: MappingAccessibleBase[KeyT, float],
        key: KeyT | Sentinel | Term[KeyT | Sentinel],
        default: float | Sentinel | None = None,
    ) -> FloatRef: ...

    @overload
    def get_item(
        self: MappingAccessibleBase[KeyT, bytes],
        key: KeyT | Sentinel | Term[KeyT | Sentinel],
        default: bytes | Sentinel | None = None,
    ) -> BytesRef: ...

    @overload
    def get_item(
        self: MappingAccessibleBase[KeyT, None],
        key: KeyT | Sentinel | Term[KeyT | Sentinel],
        default: None | Sentinel = None,
    ) -> NoneRef: ...

    @overload
    def get_item[V](
        self: MappingAccessibleBase[KeyT, list[V]],
        key: KeyT | Sentinel | Term[KeyT | Sentinel],
        default: list[V] | Sentinel | None = None,
    ) -> ListRef[V]: ...

    @overload
    def get_item[K, V](
        self: MappingAccessibleBase[KeyT, dict[K, V]],
        key: KeyT | Sentinel | Term[KeyT | Sentinel],
        default: dict[K, V] | Sentinel | None = None,
    ) -> DictRef[K, V]: ...

    @overload
    def get_item[V](
        self: MappingAccessibleBase[KeyT, set[V]],
        key: KeyT | Sentinel | Term[KeyT | Sentinel],
        default: set[V] | Sentinel | None = None,
    ) -> SetRef[V]: ...

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
        from every_pv.morphisms import GetByKeyOp

        return typed_ref(self.value_type, GetByKeyOp(self, key, default))

    @overload
    def set_item(
        self: MappingAccessibleBase[KeyT, int],
        key: KeyT | Sentinel | Term[KeyT | Sentinel],
        value: int | Sentinel | Term[int | Sentinel],
    ) -> IntRef: ...

    @overload
    def set_item(
        self: MappingAccessibleBase[KeyT, str],
        key: KeyT | Sentinel | Term[KeyT | Sentinel],
        value: str | Sentinel | Term[str | Sentinel],
    ) -> StrRef: ...

    @overload
    def set_item(
        self: MappingAccessibleBase[KeyT, bool],
        key: KeyT | Sentinel | Term[KeyT | Sentinel],
        value: bool | Sentinel | Term[bool | Sentinel],
    ) -> BoolRef: ...

    @overload
    def set_item(
        self: MappingAccessibleBase[KeyT, float],
        key: KeyT | Sentinel | Term[KeyT | Sentinel],
        value: float | Sentinel | Term[float | Sentinel],
    ) -> FloatRef: ...

    @overload
    def set_item(
        self: MappingAccessibleBase[KeyT, bytes],
        key: KeyT | Sentinel | Term[KeyT | Sentinel],
        value: bytes | Sentinel | Term[bytes | Sentinel],
    ) -> BytesRef: ...

    @overload
    def set_item(
        self: MappingAccessibleBase[KeyT, None],
        key: KeyT | Sentinel | Term[KeyT | Sentinel],
        value: None | Sentinel | Term[None | Sentinel],
    ) -> NoneRef: ...

    @overload
    def set_item[V](
        self: MappingAccessibleBase[KeyT, list[V]],
        key: KeyT | Sentinel | Term[KeyT | Sentinel],
        value: list[V] | Sentinel | Term[list[V] | Sentinel],
    ) -> ListRef[V]: ...

    @overload
    def set_item[K, V](
        self: MappingAccessibleBase[KeyT, dict[K, V]],
        key: KeyT | Sentinel | Term[KeyT | Sentinel],
        value: dict[K, V] | Sentinel | Term[dict[K, V] | Sentinel],
    ) -> DictRef[K, V]: ...

    @overload
    def set_item[V](
        self: MappingAccessibleBase[KeyT, set[V]],
        key: KeyT | Sentinel | Term[KeyT | Sentinel],
        value: set[V] | Sentinel | Term[set[V] | Sentinel],
    ) -> SetRef[V]: ...

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
        from every_pv.morphisms import SetByKeyCmd

        return typed_ref(self.value_type, SetByKeyCmd(self, key, ensure_term(value)))

    def remove_item(self, key: KeyT | Sentinel | Term[KeyT | Sentinel]) -> NoneRef:
        """Remove key from mapping.

        Args:
            key: Key to remove

        Returns:
            NoneRef (remove returns None after execution)

        Note:
            Raises KeyError at execution if key not found.

        Example:
            >>> dict_ref.remove_item("key").execute(ctx)
        """
        from every_pv.morphisms import RemoveByKeyCmd

        return NoneRef(RemoveByKeyCmd(self, key))
