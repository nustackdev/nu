"""itertools module-level functions.

Mirrors Python's ``itertools`` 1-1. Each function presents Python's argument
order and returns the shape that matches the host:

- every iterator-producing member -> its stream atom in the ``Iterator``
  form, so the result keeps chaining (``.map(...)``, ``.to_list()``) and
  still composes with ``Collect`` / ``Map`` / another itertools call (a
  form takes its body's cardinality, so the result is a stream)
- ``tee`` -> ``Object`` (it returns a *tuple* of iterators, not a stream)

This is a gap-fill: members Nu core already covers (``map`` / ``filter`` /
``zip`` / ``sorted`` / ``enumerate`` / ``reversed`` / sums and folds) are not
re-implemented here.

Each function builds its interaction atom (lazily imported, like ``nustd.math``)
and returns it. Iterable arguments are lifted into a stream child with
``Iter`` when they yield one value (a list, a ``List``, a ref), and passed
through when they already yield a stream (another itertools result, an
``Iterator``, a ``Snapshot`` over a stream, a stream action). Higher-order members take
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
from nu.forms import Iterator, Object
from nu.lang import Cardinality, cardinality_of


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

    Asks the term's resolved cardinality, not its class: anything that
    already yields a stream (another itertools result, ``Iter``, ``Map``, an
    ``Iterator`` form, a ``Snapshot`` over a stream, a stream action) is
    reused directly, since wrapping it in another ``Iter`` would feed a
    stream to a scalar consumer. Any other iterable (a list, range, ``List``,
    raw value) is opened with ``Iter``.
    """
    if cardinality_of(iterable) is Cardinality.STREAM:
        return cast("Nu", iterable)
    return Iter(iterable)


# --- infinite sources -------------------------------------------------------


def count(start: IntArg = 0, step: IntArg = 1) -> Iterator:
    """Count from ``start`` by ``step`` forever: mirrors ``itertools.count()``.

    Infinite - bound it with ``islice`` (or another short consumer).
    """
    from .interactions import Count

    return Iterator(Count(start, step))


def cycle(iterable: Arg[Iterable]) -> Iterator:
    """Repeat ``iterable`` endlessly: mirrors ``itertools.cycle()``."""
    from .interactions import Cycle

    return Iterator(Cycle(_stream(iterable)))


def repeat(elem: object, times: IntArg | None = None) -> Iterator:
    """Yield ``elem`` ``times`` times, or forever: mirrors ``itertools.repeat()``."""
    from .interactions import Repeat

    if times is None:
        return Iterator(Repeat(elem))
    return Iterator(Repeat(elem, times))


# --- pure combinators -------------------------------------------------------


def chain(*iterables: Arg[Iterable]) -> Iterator:
    """Concatenate ``iterables`` end to end: mirrors ``itertools.chain()``."""
    from .interactions import Chain

    return Iterator(Chain(*(_stream(it) for it in iterables)))


def chain_from_iterable(iterable: Arg[Iterable]) -> Iterator:
    """Flatten an iterable of iterables one level: ``itertools.chain.from_iterable()``."""
    from .interactions import ChainFromIterable

    return Iterator(ChainFromIterable(_stream(iterable)))


def islice(iterable: Arg[Iterable], *args: IntArg) -> Iterator:
    """Slice ``iterable`` lazily: mirrors ``itertools.islice()``.

    ``args`` is 1-3 ints: ``stop`` | ``start, stop`` | ``start, stop, step``.
    """
    from .interactions import Islice

    return Iterator(Islice(_stream(iterable), *args))


def compress(data: Arg[Iterable], selectors: Arg[Iterable]) -> Iterator:
    """Keep ``data`` items where ``selectors`` is truthy: ``itertools.compress()``."""
    from .interactions import Compress

    return Iterator(Compress(_stream(data), _stream(selectors)))


def pairwise(iterable: Arg[Iterable]) -> Iterator:
    """Yield overlapping consecutive pairs: mirrors ``itertools.pairwise()``."""
    from .interactions import Pairwise

    return Iterator(Pairwise(_stream(iterable)))


def batched(iterable: Arg[Iterable], n: IntArg) -> Iterator:
    """Yield tuples of up to ``n`` items: mirrors ``itertools.batched()``."""
    from .interactions import Batched

    return Iterator(Batched(_stream(iterable), n))


def zip_longest(*iterables: Arg[Iterable], fillvalue: object = None) -> Iterator:
    """Zip to the longest, padding with ``fillvalue``: ``itertools.zip_longest()``."""
    from .interactions import ZipLongest

    return Iterator(ZipLongest(*(_stream(it) for it in iterables), fillvalue))


def product(*iterables: Arg[Iterable], repeat: IntArg = 1) -> Iterator:
    """The cartesian product of ``iterables``: mirrors ``itertools.product()``."""
    from .interactions import Product

    return Iterator(Product(*(_stream(it) for it in iterables), repeat))


def permutations(iterable: Arg[Iterable], r: IntArg | None = None) -> Iterator:
    """``r``-length ordered arrangements: mirrors ``itertools.permutations()``."""
    from .interactions import Permutations

    if r is None:
        return Iterator(Permutations(_stream(iterable)))
    return Iterator(Permutations(_stream(iterable), r))


def combinations(iterable: Arg[Iterable], r: IntArg) -> Iterator:
    """``r``-length sorted subsequences: mirrors ``itertools.combinations()``."""
    from .interactions import Combinations

    return Iterator(Combinations(_stream(iterable), r))


def combinations_with_replacement(iterable: Arg[Iterable], r: IntArg) -> Iterator:
    """``r``-length subsequences allowing repeats: ``combinations_with_replacement()``."""
    from .interactions import CombinationsWithReplacement

    return Iterator(CombinationsWithReplacement(_stream(iterable), r))


# --- higher-order -----------------------------------------------------------


def takewhile(predicate: Step, iterable: Arg[Iterable]) -> Iterator:
    """Yield while ``predicate`` holds, stop at the first falsy: ``itertools.takewhile()``.

    ``predicate`` is a lambda over the item, or a tree reading it via
    ``Attr("item")``.

    Example:
        >>> nu.run(nu.Collect(nustd.itertools.takewhile(lambda x: x < 3, [1, 2, 5, 1])))[0]
        [1, 2]
    """
    from .interactions import TakeWhile

    return Iterator(TakeWhile(_stream(iterable), predicate))


def dropwhile(predicate: Step, iterable: Arg[Iterable]) -> Iterator:
    """Skip while ``predicate`` holds, then yield the rest: ``itertools.dropwhile()``.

    ``predicate`` is a lambda over the item, or a tree reading it via
    ``Attr("item")``.

    Example:
        >>> nu.run(nu.Collect(nustd.itertools.dropwhile(lambda x: x < 3, [1, 2, 5, 1])))[0]
        [5, 1]
    """
    from .interactions import DropWhile

    return Iterator(DropWhile(_stream(iterable), predicate))


def filterfalse(predicate: Step, iterable: Arg[Iterable]) -> Iterator:
    """Keep items where ``predicate`` is falsy: mirrors ``itertools.filterfalse()``.

    ``predicate`` is a lambda over the item, or a tree reading it via
    ``Attr("item")``.

    Example:
        >>> nu.run(nu.Collect(nustd.itertools.filterfalse(lambda x: x > 1, [1, 2, 3])))[0]
        [1]
    """
    from .interactions import FilterFalse

    return Iterator(FilterFalse(_stream(iterable), predicate))


def accumulate(iterable: Arg[Iterable], func: Step2 | None = None) -> Iterator:
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
        return Iterator(Accumulate(_stream(iterable)))
    return Iterator(Accumulate(_stream(iterable), func))


def starmap(function: Step, iterable: Arg[Iterable]) -> Iterator:
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

    return Iterator(StarMap(_stream(iterable), function))


def groupby(iterable: Arg[Iterable], key: Step | None = None) -> Iterator:
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
        return Iterator(GroupBy(_stream(iterable)))
    return Iterator(GroupBy(_stream(iterable), key))


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
