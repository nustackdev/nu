"""itertools module-level functions.

Mirrors Python's ``itertools`` 1-1. Each function presents Python's argument
order and returns the Form that matches the host shape:

- every iterator-producing member -> ``IteratorForm`` (materialize with a
  ``CollectQuery`` over the stream; stream-aware ``.to_list()`` is a pending
  core wiring - see the package note)
- ``tee`` -> ``AnyForm`` (it returns a *tuple* of iterators, not a stream)

This is a gap-fill: members Nu core already covers (``map`` / ``filter`` /
``zip`` / ``sorted`` / ``enumerate`` / ``reversed`` / sums and folds) are not
re-implemented here.

Each function builds its interaction atom (lazily imported, like ``nu.std.math``)
and wraps it. Iterable arguments are lifted into a stream child with
``IterQuery`` so the atom's source child carries STREAM cardinality, the way
core stream atoms compose. Higher-order members (``takewhile`` / ``dropwhile`` /
``filterfalse`` / ``accumulate`` / ``starmap`` / ``groupby``) take their
predicate/function as a Nu term that reads the current item via an
``AttrRef("item")`` (and the running value via ``AttrRef("acc")`` for
``accumulate``).
"""

from __future__ import annotations

from typing import TYPE_CHECKING, cast

from nu import AnyForm, IteratorForm
from nu.core import IterQuery


if TYPE_CHECKING:
    from collections.abc import Iterable

    from nu.lang import Arg, IntArg, Nu


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

    An ``IteratorForm`` (the result of another itertools/core stream member) is
    already a stream wrapper, so its inner ``StreamQuery`` child is reused
    directly - wrapping it in another ``IterQuery`` would feed a stream to a
    scalar consumer. Any other iterable (a list, range, ``ListForm``, raw value)
    is opened with ``IterQuery``.
    """
    if isinstance(iterable, IteratorForm):
        return cast("Nu", iterable._children[0])
    return IterQuery(iterable)


# --- infinite sources -------------------------------------------------------


def count(start: IntArg = 0, step: IntArg = 1) -> IteratorForm:
    """Count from ``start`` by ``step`` forever: mirrors ``itertools.count()``.

    Infinite - bound it with ``islice`` (or another short consumer).
    """
    from .interactions import Count

    return IteratorForm(Count(start, step))


def cycle(iterable: Arg[Iterable]) -> IteratorForm:
    """Repeat ``iterable`` endlessly: mirrors ``itertools.cycle()``."""
    from .interactions import Cycle

    return IteratorForm(Cycle(_stream(iterable)))


def repeat(elem: object, times: IntArg | None = None) -> IteratorForm:
    """Yield ``elem`` ``times`` times, or forever: mirrors ``itertools.repeat()``."""
    from .interactions import Repeat

    if times is None:
        return IteratorForm(Repeat(elem))
    return IteratorForm(Repeat(elem, times))


# --- pure combinators -------------------------------------------------------


def chain(*iterables: Arg[Iterable]) -> IteratorForm:
    """Concatenate ``iterables`` end to end: mirrors ``itertools.chain()``."""
    from .interactions import Chain

    return IteratorForm(Chain(*(_stream(it) for it in iterables)))


def chain_from_iterable(iterable: Arg[Iterable]) -> IteratorForm:
    """Flatten an iterable of iterables one level: ``itertools.chain.from_iterable()``."""
    from .interactions import ChainFromIterable

    return IteratorForm(ChainFromIterable(_stream(iterable)))


def islice(iterable: Arg[Iterable], *args: IntArg) -> IteratorForm:
    """Slice ``iterable`` lazily: mirrors ``itertools.islice()``.

    ``args`` is 1-3 ints: ``stop`` | ``start, stop`` | ``start, stop, step``.
    """
    from .interactions import Islice

    return IteratorForm(Islice(_stream(iterable), *args))


def compress(data: Arg[Iterable], selectors: Arg[Iterable]) -> IteratorForm:
    """Keep ``data`` items where ``selectors`` is truthy: ``itertools.compress()``."""
    from .interactions import Compress

    return IteratorForm(Compress(_stream(data), _stream(selectors)))


def pairwise(iterable: Arg[Iterable]) -> IteratorForm:
    """Yield overlapping consecutive pairs: mirrors ``itertools.pairwise()``."""
    from .interactions import Pairwise

    return IteratorForm(Pairwise(_stream(iterable)))


def batched(iterable: Arg[Iterable], n: IntArg) -> IteratorForm:
    """Yield tuples of up to ``n`` items: mirrors ``itertools.batched()``."""
    from .interactions import Batched

    return IteratorForm(Batched(_stream(iterable), n))


def zip_longest(*iterables: Arg[Iterable], fillvalue: object = None) -> IteratorForm:
    """Zip to the longest, padding with ``fillvalue``: ``itertools.zip_longest()``."""
    from .interactions import ZipLongest

    return IteratorForm(ZipLongest(*(_stream(it) for it in iterables), fillvalue))


def product(*iterables: Arg[Iterable], repeat: IntArg = 1) -> IteratorForm:
    """The cartesian product of ``iterables``: mirrors ``itertools.product()``."""
    from .interactions import Product

    return IteratorForm(Product(*(_stream(it) for it in iterables), repeat))


def permutations(iterable: Arg[Iterable], r: IntArg | None = None) -> IteratorForm:
    """``r``-length ordered arrangements: mirrors ``itertools.permutations()``."""
    from .interactions import Permutations

    if r is None:
        return IteratorForm(Permutations(_stream(iterable)))
    return IteratorForm(Permutations(_stream(iterable), r))


def combinations(iterable: Arg[Iterable], r: IntArg) -> IteratorForm:
    """``r``-length sorted subsequences: mirrors ``itertools.combinations()``."""
    from .interactions import Combinations

    return IteratorForm(Combinations(_stream(iterable), r))


def combinations_with_replacement(iterable: Arg[Iterable], r: IntArg) -> IteratorForm:
    """``r``-length subsequences allowing repeats: ``combinations_with_replacement()``."""
    from .interactions import CombinationsWithReplacement

    return IteratorForm(CombinationsWithReplacement(_stream(iterable), r))


# --- higher-order -----------------------------------------------------------


def takewhile(predicate: Nu, iterable: Arg[Iterable]) -> IteratorForm:
    """Yield while ``predicate`` holds, stop at the first falsy: ``itertools.takewhile()``.

    ``predicate`` reads the current item via ``AttrRef("item")``.
    """
    from .interactions import TakeWhile

    return IteratorForm(TakeWhile(_stream(iterable), predicate))


def dropwhile(predicate: Nu, iterable: Arg[Iterable]) -> IteratorForm:
    """Skip while ``predicate`` holds, then yield the rest: ``itertools.dropwhile()``.

    ``predicate`` reads the current item via ``AttrRef("item")``.
    """
    from .interactions import DropWhile

    return IteratorForm(DropWhile(_stream(iterable), predicate))


def filterfalse(predicate: Nu, iterable: Arg[Iterable]) -> IteratorForm:
    """Keep items where ``predicate`` is falsy: mirrors ``itertools.filterfalse()``.

    ``predicate`` reads the current item via ``AttrRef("item")``.
    """
    from .interactions import FilterFalse

    return IteratorForm(FilterFalse(_stream(iterable), predicate))


def accumulate(iterable: Arg[Iterable], func: Nu | None = None) -> IteratorForm:
    """Running accumulation: mirrors ``itertools.accumulate()``.

    Without ``func`` it is a running sum. With ``func`` (a Nu term) each step
    reads the running value via ``AttrRef("acc")`` and the item via
    ``AttrRef("item")``; the first item is yielded as-is.
    """
    from .interactions import Accumulate

    if func is None:
        return IteratorForm(Accumulate(_stream(iterable)))
    return IteratorForm(Accumulate(_stream(iterable), func))


def starmap(function: Nu, iterable: Arg[Iterable]) -> IteratorForm:
    """Apply ``function`` to unpacked items: mirrors ``itertools.starmap()``.

    Each item is a tuple; ``function`` reads its parts via
    ``TupleAttrRef("item")[0]``, ``[1]``, ...
    """
    from .interactions import StarMap

    return IteratorForm(StarMap(_stream(iterable), function))


def groupby(iterable: Arg[Iterable], key: Nu | None = None) -> IteratorForm:
    """Group consecutive items by ``key``: mirrors ``itertools.groupby()``.

    Yields ``(key_value, tuple(group))`` pairs. With ``key`` (a Nu term) the key
    reads the item via ``AttrRef("item")``; without it items group by identity.
    """
    from .interactions import GroupBy

    if key is None:
        return IteratorForm(GroupBy(_stream(iterable)))
    return IteratorForm(GroupBy(_stream(iterable), key))


# --- tee --------------------------------------------------------------------


def tee(iterable: Arg[Iterable], n: IntArg = 2) -> AnyForm:
    """Split ``iterable`` into ``n`` independent iterators: ``itertools.tee()``.

    Returns an ``AnyForm`` holding a *tuple* of ``n`` iterators (not a stream),
    so it is the one member here backed by a ``ScalarQuery``. Its source rides
    as a scalar child (a ``ScalarQuery`` may not hold a stream), and the atom
    materializes it with ``sync_iter`` before splitting.
    """
    from .interactions import Tee

    return AnyForm(Tee(iterable, n))
