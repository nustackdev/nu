"""Standalone functional morphisms for iterable composition.

All operations as standalone functions, not methods on types.
Follows Python stdlib naming for intuitive navigation.

Transformations (lazy-conceptual, eager execution):
    Map(iterable, fn) -> ListValue
    Filter(iterable, pred) -> ListValue
    Sorted(iterable, reverse=False) -> ListValue
    Reversed(iterable) -> ListValue
    Flatten(iterable) -> ListValue
    Unique(iterable, key=None) -> ListValue
    Pluck(iterable, field) -> ListValue
    FilterBy(iterable, field, value) -> ListValue

Combinators:
    Zip(*iterables) -> ListValue[tuple]
    Chain(*iterables) -> ListValue
    Enumerate(iterable, start=0) -> ListValue[tuple[int, T]]

Slicing:
    Take(iterable, n) -> ListValue
    Drop(iterable, n) -> ListValue

Grouping:
    GroupBy(iterable, key_fn) -> ListValue[tuple[K, list]]
    Partition(iterable, predicate) -> TupleValue[list, list]

Reductions (terminal):
    Reduce(iterable, fn, initial) -> AnyValue
    Sum(iterable) -> AnyValue
    Min(iterable, key=None) -> AnyValue
    Max(iterable, key=None) -> AnyValue
    Any(iterable) -> BoolValue
    All(iterable) -> BoolValue

Converters:
    ToList(iterable) -> ListValue
    ToSet(iterable) -> SetValue
    ToDict(iterable, key_fn, val_fn) -> DictValue
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from ..utils import ensure_term


if TYPE_CHECKING:
    from collections.abc import Callable

    from ..values import AnyValue, BoolValue, DictValue, ListValue, SetValue, TupleValue


__all__ = [  # noqa: RUF022
    # Transformations
    "Map",
    "Filter",
    "Sorted",
    "Reversed",
    "Flatten",
    "Unique",
    "Pluck",
    "FilterBy",
    # Combinators
    "Zip",
    "Chain",
    "Enumerate",
    # Slicing
    "Take",
    "Drop",
    # Grouping
    "GroupBy",
    "Partition",
    # Reductions
    "Reduce",
    "Sum",
    "Min",
    "Max",
    "Any",
    "All",
    # Converters
    "ToList",
    "ToSet",
    "ToDict",
]


# =============================================================================
# TRANSFORMATIONS
# =============================================================================


def Map(iterable: object, fn: Callable) -> ListValue:  # noqa: N802
    """Map function over iterable elements.

    Example::

        Map(prices, lambda x: x * 2)
        Map(names, str.upper)
    """
    from ..morphisms.itertools.transform import MapOp
    from ..values import ListValue

    return ListValue(MapOp(ensure_term(iterable), fn))


def Filter(iterable: object, predicate: Callable) -> ListValue:  # noqa: N802
    """Filter iterable by predicate.

    Example::

        Filter(prices, lambda x: x > 100)
        Filter(items, bool)  # remove falsy
    """
    from ..morphisms.itertools.transform import FilterOp
    from ..values import ListValue

    return ListValue(FilterOp(ensure_term(iterable), predicate))


def Sorted(iterable: object, *, reverse: object = False) -> ListValue:  # noqa: N802
    """Sorted iterable.

    Example::

        Sorted(prices)
        Sorted(prices, reverse=True)
    """
    from ..morphisms.itertools.transform import SortedOp
    from ..values import ListValue

    return ListValue(SortedOp(ensure_term(iterable), ensure_term(reverse)))


def Reversed(iterable: object) -> ListValue:  # noqa: N802
    """Reversed sequence.

    Example::

        Reversed(items)
    """
    from ..morphisms.itertools.transform import ReversedOp
    from ..values import ListValue

    return ListValue(ReversedOp(ensure_term(iterable)))


def Flatten(iterable: object) -> ListValue:  # noqa: N802
    """Flatten one level of nesting.

    Example::

        Flatten([[1, 2], [3, 4]])  # -> [1, 2, 3, 4]
    """
    from ..morphisms.itertools.transform import FlattenOp
    from ..values import ListValue

    return ListValue(FlattenOp(ensure_term(iterable)))


def Unique(iterable: object, *, key: Callable | None = None) -> ListValue:  # noqa: N802
    """Unique elements preserving order.

    Example::

        Unique([1, 2, 2, 3])  # -> [1, 2, 3]
        Unique(items, key=lambda x: x["id"])
    """
    from ..morphisms.itertools.transform import UniqueOp
    from ..values import ListValue

    return ListValue(UniqueOp(ensure_term(iterable), key))


def Pluck(iterable: object, field: object) -> ListValue:  # noqa: N802
    """Extract field from each element.

    Example::

        Pluck(users, "name")  # -> ["alice", "bob"]
    """
    from ..morphisms.itertools.transform import PluckOp
    from ..values import ListValue

    return ListValue(PluckOp(ensure_term(iterable), ensure_term(field)))


def FilterBy(iterable: object, field: object, value: object) -> ListValue:  # noqa: N802
    """Filter elements where field equals value.

    Example::

        FilterBy(users, "role", "admin")
    """
    from ..morphisms.itertools.transform import FilterByOp
    from ..values import ListValue

    return ListValue(FilterByOp(ensure_term(iterable), ensure_term(field), ensure_term(value)))


# =============================================================================
# COMBINATORS
# =============================================================================


def Zip(*iterables: object) -> ListValue:  # noqa: N802
    """Zip multiple iterables together.

    Example::

        Zip(names, ages)  # -> [("alice", 30), ("bob", 25)]
    """
    from ..morphisms.itertools.combine import ZipOp
    from ..values import ListValue

    return ListValue(ZipOp(*(ensure_term(it) for it in iterables)))


def Chain(*iterables: object) -> ListValue:  # noqa: N802
    """Chain multiple iterables into one.

    Example::

        Chain([1, 2], [3, 4])  # -> [1, 2, 3, 4]
    """
    from ..morphisms.itertools.combine import ChainOp
    from ..values import ListValue

    return ListValue(ChainOp(*(ensure_term(it) for it in iterables)))


def Enumerate(iterable: object, start: object = 0) -> ListValue:  # noqa: N802
    """Enumerate iterable with index.

    Example::

        Enumerate(items)  # -> [(0, a), (1, b), ...]
        Enumerate(items, start=1)
    """
    from ..morphisms.itertools.combine import EnumerateOp
    from ..values import ListValue

    return ListValue(EnumerateOp(ensure_term(iterable), ensure_term(start)))


# =============================================================================
# SLICING
# =============================================================================


def Take(iterable: object, n: object) -> ListValue:  # noqa: N802
    """Take first N elements.

    Example::

        Take(items, 5)
    """
    from ..morphisms.itertools.slice import TakeOp
    from ..values import ListValue

    return ListValue(TakeOp(ensure_term(iterable), ensure_term(n)))


def Drop(iterable: object, n: object) -> ListValue:  # noqa: N802
    """Drop first N elements.

    Example::

        Drop(items, 5)
    """
    from ..morphisms.itertools.slice import DropOp
    from ..values import ListValue

    return ListValue(DropOp(ensure_term(iterable), ensure_term(n)))


# =============================================================================
# GROUPING
# =============================================================================


def GroupBy(iterable: object, key_fn: Callable) -> ListValue:  # noqa: N802
    """Group elements by key function.

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
    """Partition into (matches, non_matches).

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
    """Reduce iterable to single value.

    Example::

        Reduce(prices, lambda acc, x: acc + x, 0)
    """
    from ..morphisms.itertools.reduce import ReduceOp
    from ..values import AnyValue

    return AnyValue(ReduceOp(ensure_term(iterable), fn, initial))


def Sum(iterable: object) -> AnyValue:  # noqa: N802
    """Sum all elements.

    Example::

        Sum(prices)
    """
    from ..morphisms.itertools.reduce import SumOp
    from ..values import AnyValue

    return AnyValue(SumOp(ensure_term(iterable)))


def Min(iterable: object, *, key: Callable | None = None) -> AnyValue:  # noqa: N802
    """Get minimum element.

    Example::

        Min(prices)
        Min(users, key=lambda u: u["age"])
    """
    from ..morphisms.itertools.reduce import MinOp
    from ..values import AnyValue

    return AnyValue(MinOp(ensure_term(iterable), key))


def Max(iterable: object, *, key: Callable | None = None) -> AnyValue:  # noqa: N802
    """Get maximum element.

    Example::

        Max(prices)
        Max(users, key=lambda u: u["age"])
    """
    from ..morphisms.itertools.reduce import MaxOp
    from ..values import AnyValue

    return AnyValue(MaxOp(ensure_term(iterable), key))


def Any(iterable: object) -> BoolValue:  # noqa: N802
    """Check if any element is truthy.

    Example::

        Any(flags)
    """
    from ..morphisms.itertools.reduce import AnyOp
    from ..values import BoolValue

    return BoolValue(AnyOp(ensure_term(iterable)))


def All(iterable: object) -> BoolValue:  # noqa: N802
    """Check if all elements are truthy.

    Example::

        All(flags)
    """
    from ..morphisms.itertools.reduce import AllOp
    from ..values import BoolValue

    return BoolValue(AllOp(ensure_term(iterable)))


# =============================================================================
# CONVERTERS
# =============================================================================


def ToList(iterable: object) -> ListValue:  # noqa: N802
    """Materialize iterable to list.

    Example::

        ToList(some_iterable)
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
    """Build dict from iterable using key/value extractors.

    Example::

        ToDict(users, lambda u: u["id"], lambda u: u["name"])
    """
    from ..morphisms.itertools.transform import ToDictOp
    from ..values import DictValue

    return DictValue(ToDictOp(ensure_term(iterable), key_fn, val_fn))
