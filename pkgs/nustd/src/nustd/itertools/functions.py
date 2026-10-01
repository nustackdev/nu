"""itertools module-level functions.

Mirrors Python's ``itertools`` 1-1. Each function presents Python's argument
order and returns the shape that matches the host:

- every iterator-producing member -> the raw ``StreamQuery`` atom (compose
  with ``Collect`` / ``Map`` / another itertools call; cardinality
  laws line up because the atom honestly declares STREAM)
- ``tee`` -> ``Object`` (it returns a *tuple* of iterators, not a stream)

This is a gap-fill: members Nu core already covers (``map`` / ``filter`` /
``zip`` / ``sorted`` / ``enumerate`` / ``reversed`` / sums and folds) are not
re-implemented here.

Each function builds its interaction atom (lazily imported, like ``nustd.math``)
and returns it. Iterable arguments are lifted into a stream child with
``Iter`` (a scalar iterable), passed through when already a stream atom,
or unwrapped when they're an ``Iterator`` wrapper. Higher-order members take
their predicate or function the way Python does, as a lambda
(``takewhile(lambda x: x < 3, xs)``). It runs once, at construction, with refs
to what it is handed, so it builds the step and never computes with them in
Python. A plain Nu term works too, reading the current item via
``Attr("item")`` (and the running value via ``Attr("acc")`` for
``accumulate``).
"""

from __future__ import annotations

from typing import TYPE_CHECKING, cast

from nu.core import Iter
from nu.forms import Object
from nu.lang import StreamQuery


if TYPE_CHECKING:
    from collections.abc import Callable, Iterable

    from nu.context import Attr
    from nu.lang import Arg, IntArg, Nu

    Step = Nu | Callable[[Attr], Nu]
    Step2 = Nu | Callable[[Attr, Attr], Nu]


__all__ = [
    "accumulate",
    "batched",
    "chain",
    "chain_from_iterable",
    "combinations",
    "combinations_with_replacement",
    "compress",
    "count",
    "cycle",
    "dropwhile",
    "filterfalse",
    "groupby",
    "islice",
    "pairwise",
    "permutations",
    "product",
    "repeat",
    "starmap",
    "takewhile",
    "tee",
    "zip_longest",
]


def _stream(iterable: Arg[Iterable]) -> Nu:
    """Lift an iterable argument into a STREAM child.

    A ``StreamQuery`` (another itertools result, ``Iter``, ``Map``, an
    ``Iterator`` form, ...) is already stream-shaped, so it's reused
    directly - wrapping it in another ``Iter`` would feed a stream to a
    scalar consumer. Any other iterable (a list, range, ``List``, raw
    value) is opened with ``Iter``.
    """
    if isinstance(iterable, StreamQuery):
        return cast("Nu", iterable)
    return Iter(iterable)


# --- infinite sources -------------------------------------------------------


def count(start: IntArg = 0, step: IntArg = 1) -> Nu:
    """Count from ``start`` by ``step`` forever: mirrors ``itertools.count()``.

    Infinite - bound it with ``islice`` (or another short consumer).
    """
    from .interactions import Count

    return Count(start, step)


def cycle(iterable: Arg[Iterable]) -> Nu:
    """Repeat ``iterable`` endlessly: mirrors ``itertools.cycle()``."""
    from .interactions import Cycle

    return Cycle(_stream(iterable))


def repeat(elem: object, times: IntArg | None = None) -> Nu:
    """Yield ``elem`` ``times`` times, or forever: mirrors ``itertools.repeat()``."""
    from .interactions import Repeat

    if times is None:
        return Repeat(elem)
    return Repeat(elem, times)


# --- pure combinators -------------------------------------------------------


def chain(*iterables: Arg[Iterable]) -> Nu:
    """Concatenate ``iterables`` end to end: mirrors ``itertools.chain()``."""
    from .interactions import Chain

    return Chain(*(_stream(it) for it in iterables))


def chain_from_iterable(iterable: Arg[Iterable]) -> Nu:
    """Flatten an iterable of iterables one level: ``itertools.chain.from_iterable()``."""
    from .interactions import ChainFromIterable

    return ChainFromIterable(_stream(iterable))


def islice(iterable: Arg[Iterable], *args: IntArg) -> Nu:
    """Slice ``iterable`` lazily: mirrors ``itertools.islice()``.

    ``args`` is 1-3 ints: ``stop`` | ``start, stop`` | ``start, stop, step``.
    """
    from .interactions import Islice

    return Islice(_stream(iterable), *args)


def compress(data: Arg[Iterable], selectors: Arg[Iterable]) -> Nu:
    """Keep ``data`` items where ``selectors`` is truthy: ``itertools.compress()``."""
    from .interactions import Compress

    return Compress(_stream(data), _stream(selectors))


def pairwise(iterable: Arg[Iterable]) -> Nu:
    """Yield overlapping consecutive pairs: mirrors ``itertools.pairwise()``."""
    from .interactions import Pairwise

    return Pairwise(_stream(iterable))


def batched(iterable: Arg[Iterable], n: IntArg) -> Nu:
    """Yield tuples of up to ``n`` items: mirrors ``itertools.batched()``."""
    from .interactions import Batched

    return Batched(_stream(iterable), n)


def zip_longest(*iterables: Arg[Iterable], fillvalue: object = None) -> Nu:
    """Zip to the longest, padding with ``fillvalue``: ``itertools.zip_longest()``."""
    from .interactions import ZipLongest

    return ZipLongest(*(_stream(it) for it in iterables), fillvalue)


def product(*iterables: Arg[Iterable], repeat: IntArg = 1) -> Nu:
    """The cartesian product of ``iterables``: mirrors ``itertools.product()``."""
    from .interactions import Product

    return Product(*(_stream(it) for it in iterables), repeat)


def permutations(iterable: Arg[Iterable], r: IntArg | None = None) -> Nu:
    """``r``-length ordered arrangements: mirrors ``itertools.permutations()``."""
    from .interactions import Permutations

    if r is None:
        return Permutations(_stream(iterable))
    return Permutations(_stream(iterable), r)


def combinations(iterable: Arg[Iterable], r: IntArg) -> Nu:
    """``r``-length sorted subsequences: mirrors ``itertools.combinations()``."""
    from .interactions import Combinations

    return Combinations(_stream(iterable), r)


def combinations_with_replacement(iterable: Arg[Iterable], r: IntArg) -> Nu:
    """``r``-length subsequences allowing repeats: ``combinations_with_replacement()``."""
    from .interactions import CombinationsWithReplacement

    return CombinationsWithReplacement(_stream(iterable), r)


# --- higher-order -----------------------------------------------------------


def takewhile(predicate: Step, iterable: Arg[Iterable]) -> Nu:
    """Yield while ``predicate`` holds, stop at the first falsy: ``itertools.takewhile()``.

    ``predicate`` is a lambda over the item, or a tree reading it via
    ``Attr("item")``.

    Example:
        >>> nu.run(nu.Collect(nustd.itertools.takewhile(lambda x: x < 3, [1, 2, 5, 1])))[0]
        [1, 2]
    """
    from .interactions import TakeWhile

    return TakeWhile(_stream(iterable), predicate)


def dropwhile(predicate: Step, iterable: Arg[Iterable]) -> Nu:
    """Skip while ``predicate`` holds, then yield the rest: ``itertools.dropwhile()``.

    ``predicate`` is a lambda over the item, or a tree reading it via
    ``Attr("item")``.

    Example:
        >>> nu.run(nu.Collect(nustd.itertools.dropwhile(lambda x: x < 3, [1, 2, 5, 1])))[0]
        [5, 1]
    """
    from .interactions import DropWhile

    return DropWhile(_stream(iterable), predicate)


def filterfalse(predicate: Step, iterable: Arg[Iterable]) -> Nu:
    """Keep items where ``predicate`` is falsy: mirrors ``itertools.filterfalse()``.

    ``predicate`` is a lambda over the item, or a tree reading it via
    ``Attr("item")``.

    Example:
        >>> nu.run(nu.Collect(nustd.itertools.filterfalse(lambda x: x > 1, [1, 2, 3])))[0]
        [1]
    """
    from .interactions import FilterFalse

    return FilterFalse(_stream(iterable), predicate)


def accumulate(iterable: Arg[Iterable], func: Step2 | None = None) -> Nu:
    """Running accumulation: mirrors ``itertools.accumulate()``.

    Without ``func`` it is a running sum. With ``func``, a lambda over the
    running value and the item, or a tree reading them via ``Attr("acc")``
    and ``Attr("item")``, each step yields its result; the first item is
    yielded as-is.

    Example:
        >>> nu.run(nu.Collect(nustd.itertools.accumulate([1, 2, 3], lambda acc, x: nu.Int(acc) * x)))[0]
        [1, 2, 6]
    """
    from .interactions import Accumulate

    if func is None:
        return Accumulate(_stream(iterable))
    return Accumulate(_stream(iterable), func)


def starmap(function: Step, iterable: Arg[Iterable]) -> Nu:
    """Apply ``function`` to unpacked items: mirrors ``itertools.starmap()``.

    Each item is a tuple. ``function`` is a lambda over the whole tuple,
    reading its parts by index, or a tree reading them via
    ``Attr("item")[0]``, ``[1]``, ...

    Example:
        >>> pairs = [(2, 3), (4, 5)]
        >>> nu.run(nu.Collect(nustd.itertools.starmap(lambda p: nu.Int(p[0]) * p[1], pairs)))[0]
        [6, 20]
    """
    from .interactions import StarMap

    return StarMap(_stream(iterable), function)


def groupby(iterable: Arg[Iterable], key: Step | None = None) -> Nu:
    """Group consecutive items by ``key``: mirrors ``itertools.groupby()``.

    Yields ``(key_value, tuple(group))`` pairs. ``key`` is a lambda over the
    item, or a tree reading it via ``Attr("item")``; without it items group
    by identity.

    Example:
        >>> nu.run(nu.Collect(nustd.itertools.groupby([1, 3, 2], lambda x: nu.Int(x) % 2)))[0]
        [(1, (1, 3)), (0, (2,))]
    """
    from .interactions import GroupBy

    if key is None:
        return GroupBy(_stream(iterable))
    return GroupBy(_stream(iterable), key)


# --- tee --------------------------------------------------------------------


def tee(iterable: Arg[Iterable], n: IntArg = 2) -> Object:
    """Split ``iterable`` into ``n`` independent iterators: ``itertools.tee()``.

    Returns an ``Object`` holding a *tuple* of ``n`` iterators (not a stream),
    so it is the one member here backed by a ``ScalarQuery``. Its source rides
    as a scalar child (a ``ScalarQuery`` may not hold a stream), and the atom
    materializes it with ``sync_iter`` before splitting.
    """
    from .interactions import Tee

    return Object(Tee(iterable, n))
