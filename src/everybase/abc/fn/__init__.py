"""Standalone functional morphisms for iterable composition.

All operations as standalone functions, not methods on types.
Follows Python stdlib naming for intuitive navigation.

Transformations (lazy — return IteratorValue):
    Map(iterable, fn) -> IteratorValue
    Filter(iterable, pred) -> IteratorValue
    Reversed(iterable) -> IteratorValue
    Flatten(iterable) -> IteratorValue
    Unique(iterable, key=None) -> IteratorValue
    Pluck(iterable, field) -> IteratorValue
    FilterBy(iterable, field, value) -> IteratorValue

Combinators (lazy — return IteratorValue):
    Zip(*iterables) -> IteratorValue[tuple]
    Chain(*iterables) -> IteratorValue
    Enumerate(iterable, start=0) -> IteratorValue[tuple[int, T]]

Slicing (lazy — return IteratorValue):
    Take(iterable, n) -> IteratorValue
    Drop(iterable, n) -> IteratorValue

Terminals (eager — return concrete values):
    Sorted(iterable, reverse=False) -> ListValue
    GroupBy(iterable, key_fn) -> ListValue[tuple[K, list]]
    Partition(iterable, predicate) -> TupleValue[list, list]
    Reduce(iterable, fn, initial) -> AnyValue
    Sum(iterable) -> AnyValue
    Min(iterable, key=None) -> AnyValue
    Max(iterable, key=None) -> AnyValue
    Any(iterable) -> BoolValue
    All(iterable) -> BoolValue

Builtins (standalone equivalents of Python builtins):
    Len(obj) -> IntValue
    Contains(collection, item) -> BoolValue

Materializers (eager — consume iterators into collections):
    ToList(iterable) -> ListValue
    ToSet(iterable) -> SetValue
    ToDict(iterable, key_fn, val_fn) -> DictValue
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from ..utils import ensure_term


if TYPE_CHECKING:
    from collections.abc import Callable

    from ..values import (
        AnyValue,
        BoolValue,
        DictValue,
        IntValue,
        IteratorValue,
        ListValue,
        SetValue,
        TupleValue,
    )


__all__ = [  # noqa: RUF022
    # Transformations (lazy)
    "Map",
    "Filter",
    "Reversed",
    "Flatten",
    "Unique",
    "Pluck",
    "FilterBy",
    # Combinators (lazy)
    "Zip",
    "Chain",
    "Enumerate",
    # Slicing (lazy)
    "Take",
    "Drop",
    # Terminals (eager)
    "Sorted",
    "GroupBy",
    "Partition",
    "Reduce",
    "Sum",
    "Min",
    "Max",
    "Any",
    "All",
    # Builtins
    "Len",
    "Contains",
    # Materializers
    "ToList",
    "ToSet",
    "ToDict",
]


# =============================================================================
# TRANSFORMATIONS (lazy — return IteratorValue)
# =============================================================================


def Map(iterable: object, fn: Callable) -> IteratorValue:  # noqa: N802
    """Map function over iterable elements. Lazy.

    Example::

        Map(prices, lambda x: x * 2)
        Map(names, str.upper)
    """
    from ..morphisms.itertools.transform import MapOp
    from ..values import IteratorValue

    return IteratorValue(MapOp(ensure_term(iterable), fn))


def Filter(iterable: object, predicate: Callable) -> IteratorValue:  # noqa: N802
    """Filter iterable by predicate. Lazy.

    Example::

        Filter(prices, lambda x: x > 100)
        Filter(items, bool)  # remove falsy
    """
    from ..morphisms.itertools.transform import FilterOp
    from ..values import IteratorValue

    return IteratorValue(FilterOp(ensure_term(iterable), predicate))


def Reversed(iterable: object) -> IteratorValue:  # noqa: N802
    """Reversed sequence. Lazy.

    Example::

        Reversed(items)
    """
    from ..morphisms.itertools.transform import ReversedOp
    from ..values import IteratorValue

    return IteratorValue(ReversedOp(ensure_term(iterable)))


def Flatten(iterable: object) -> IteratorValue:  # noqa: N802
    """Flatten one level of nesting. Lazy.

    Example::

        Flatten([[1, 2], [3, 4]])  # -> iter(1, 2, 3, 4)
    """
    from ..morphisms.itertools.transform import FlattenOp
    from ..values import IteratorValue

    return IteratorValue(FlattenOp(ensure_term(iterable)))


def Unique(iterable: object, *, key: Callable | None = None) -> IteratorValue:  # noqa: N802
    """Unique elements preserving order. Lazy.

    Example::

        Unique([1, 2, 2, 3])  # -> iter(1, 2, 3)
        Unique(items, key=lambda x: x["id"])
    """
    from ..morphisms.itertools.transform import UniqueOp
    from ..values import IteratorValue

    return IteratorValue(UniqueOp(ensure_term(iterable), key))


def Pluck(iterable: object, field: object) -> IteratorValue:  # noqa: N802
    """Extract field from each element. Lazy.

    Example::

        Pluck(users, "name")  # -> iter("alice", "bob")
    """
    from ..morphisms.itertools.transform import PluckOp
    from ..values import IteratorValue

    return IteratorValue(PluckOp(ensure_term(iterable), ensure_term(field)))


def FilterBy(iterable: object, field: object, value: object) -> IteratorValue:  # noqa: N802
    """Filter elements where field equals value. Lazy.

    Example::

        FilterBy(users, "role", "admin")
    """
    from ..morphisms.itertools.transform import FilterByOp
    from ..values import IteratorValue

    return IteratorValue(FilterByOp(ensure_term(iterable), ensure_term(field), ensure_term(value)))


# =============================================================================
# COMBINATORS (lazy — return IteratorValue)
# =============================================================================


def Zip(*iterables: object) -> IteratorValue:  # noqa: N802
    """Zip multiple iterables together. Lazy.

    Example::

        Zip(names, ages)  # -> iter(("alice", 30), ("bob", 25))
    """
    from ..morphisms.itertools.combine import ZipOp
    from ..values import IteratorValue

    return IteratorValue(ZipOp(*(ensure_term(it) for it in iterables)))


def Chain(*iterables: object) -> IteratorValue:  # noqa: N802
    """Chain multiple iterables into one. Lazy.

    Example::

        Chain([1, 2], [3, 4])  # -> iter(1, 2, 3, 4)
    """
    from ..morphisms.itertools.combine import ChainOp
    from ..values import IteratorValue

    return IteratorValue(ChainOp(*(ensure_term(it) for it in iterables)))


def Enumerate(iterable: object, start: object = 0) -> IteratorValue:  # noqa: N802
    """Enumerate iterable with index. Lazy.

    Example::

        Enumerate(items)  # -> iter((0, a), (1, b), ...)
        Enumerate(items, start=1)
    """
    from ..morphisms.itertools.combine import EnumerateOp
    from ..values import IteratorValue

    return IteratorValue(EnumerateOp(ensure_term(iterable), ensure_term(start)))


# =============================================================================
# SLICING (lazy — return IteratorValue)
# =============================================================================


def Take(iterable: object, n: object) -> IteratorValue:  # noqa: N802
    """Take first N elements. Lazy.

    Example::

        Take(items, 5)
    """
    from ..morphisms.itertools.slice import TakeOp
    from ..values import IteratorValue

    return IteratorValue(TakeOp(ensure_term(iterable), ensure_term(n)))


def Drop(iterable: object, n: object) -> IteratorValue:  # noqa: N802
    """Drop first N elements. Lazy.

    Example::

        Drop(items, 5)
    """
    from ..morphisms.itertools.slice import DropOp
    from ..values import IteratorValue

    return IteratorValue(DropOp(ensure_term(iterable), ensure_term(n)))


# =============================================================================
# TERMINALS (eager — return concrete values)
# =============================================================================


def Sorted(iterable: object, *, reverse: object = False) -> ListValue:  # noqa: N802
    """Sorted iterable. Terminal — inherently eager.

    Example::

        Sorted(prices)
        Sorted(prices, reverse=True)
    """
    from ..morphisms.itertools.transform import SortedOp
    from ..values import ListValue

    return ListValue(SortedOp(ensure_term(iterable), ensure_term(reverse)))


def GroupBy(iterable: object, key_fn: Callable) -> ListValue:  # noqa: N802
    """Group elements by key function. Terminal.

    Returns list of (key, group_list) tuples. Groups elements regardless
    of input order (unlike itertools.groupby).

    Example::

        GroupBy(users, lambda u: u["role"])
        # -> [("admin", [...]), ("user", [...])]
    """
    from ..morphisms.itertools.group import GroupByOp
    from ..values import ListValue

    return ListValue(GroupByOp(ensure_term(iterable), key_fn))


def Partition(iterable: object, predicate: Callable) -> TupleValue:  # noqa: N802
    """Partition into (matches, non_matches). Terminal.

    Example::

        Partition(numbers, lambda x: x > 0)
        # -> ([1, 2, 3], [-1, -2])
    """
    from ..morphisms.itertools.group import PartitionOp
    from ..values import TupleValue

    return TupleValue(PartitionOp(ensure_term(iterable), predicate))


# =============================================================================
# REDUCTIONS (terminal)
# =============================================================================


def Reduce(iterable: object, fn: Callable, initial: object) -> AnyValue:  # noqa: N802
    """Reduce iterable to single value. Terminal.

    Example::

        Reduce(prices, lambda acc, x: acc + x, 0)
    """
    from ..morphisms.itertools.reduce import ReduceOp
    from ..values import AnyValue

    return AnyValue(ReduceOp(ensure_term(iterable), fn, initial))


def Sum(iterable: object) -> AnyValue:  # noqa: N802
    """Sum all elements. Terminal.

    Example::

        Sum(prices)
    """
    from ..morphisms.itertools.reduce import SumOp
    from ..values import AnyValue

    return AnyValue(SumOp(ensure_term(iterable)))


def Min(iterable: object, *, key: Callable | None = None) -> AnyValue:  # noqa: N802
    """Get minimum element. Terminal.

    Example::

        Min(prices)
        Min(users, key=lambda u: u["age"])
    """
    from ..morphisms.itertools.reduce import MinOp
    from ..values import AnyValue

    return AnyValue(MinOp(ensure_term(iterable), key))


def Max(iterable: object, *, key: Callable | None = None) -> AnyValue:  # noqa: N802
    """Get maximum element. Terminal.

    Example::

        Max(prices)
        Max(users, key=lambda u: u["age"])
    """
    from ..morphisms.itertools.reduce import MaxOp
    from ..values import AnyValue

    return AnyValue(MaxOp(ensure_term(iterable), key))


def Any(iterable: object) -> BoolValue:  # noqa: N802
    """Check if any element is truthy. Terminal.

    Example::

        Any(flags)
    """
    from ..morphisms.itertools.reduce import AnyOp
    from ..values import BoolValue

    return BoolValue(AnyOp(ensure_term(iterable)))


def All(iterable: object) -> BoolValue:  # noqa: N802
    """Check if all elements are truthy. Terminal.

    Example::

        All(flags)
    """
    from ..morphisms.itertools.reduce import AllOp
    from ..values import BoolValue

    return BoolValue(AllOp(ensure_term(iterable)))


# =============================================================================
# BUILTINS (standalone equivalents of Python builtins)
# =============================================================================


def Len(obj: object) -> IntValue:  # noqa: N802
    """Get length of a sized object. Like Python's ``len()``.

    Example::

        Len(my_list)
        Len(my_dict)
        Len(my_str)
    """
    from ..morphisms import LenOp
    from ..values import IntValue

    return IntValue(LenOp(ensure_term(obj)))


def Contains(collection: object, item: object) -> BoolValue:  # noqa: N802
    """Check if item is in collection. Like Python's ``in`` operator.

    Example::

        Contains(my_list, 42)
        Contains(my_str, "hello")
    """
    from ..morphisms import ContainsOp
    from ..values import BoolValue

    return BoolValue(ContainsOp(ensure_term(collection), item))


# =============================================================================
# MATERIALIZERS
# =============================================================================


def ToList(iterable: object) -> ListValue:  # noqa: N802
    """Materialize iterable to list.

    Example::

        ToList(Map(items, fn))  # explicit materialization
    """
    from ..morphisms.builtins.conversion import ToListOp
    from ..values import ListValue

    return ListValue(ToListOp(ensure_term(iterable)))


def ToSet(iterable: object) -> SetValue:  # noqa: N802
    """Materialize iterable to set.

    Example::

        ToSet(items)
    """
    from ..morphisms.builtins.conversion import ToSetOp
    from ..values import SetValue

    return SetValue(ToSetOp(ensure_term(iterable)))


def ToDict(iterable: object, key_fn: Callable, val_fn: Callable) -> DictValue:  # noqa: N802
    """Build dict from iterable using key/value extractors. Terminal.

    Example::

        ToDict(users, lambda u: u["id"], lambda u: u["name"])
    """
    from ..morphisms.itertools.transform import ToDictOp
    from ..values import DictValue

    return DictValue(ToDictOp(ensure_term(iterable), key_fn, val_fn))
