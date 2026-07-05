"""Functional tests for ``nu.std.itertools`` - drive the atoms through the engine.

Every member is asserted against the real ``itertools`` result. Iterator
results are materialized with a ``CollectQuery`` over the Form's stream child
(``IteratorForm.to_list()`` is not yet wired through the cardinality laws, so it
is not exercised here). Higher-order members build their predicate / function
from a typed ``AttrRef`` over core atoms - ``AnyAttrRef("item")``,
``AnyAttrRef("acc")``, ``TupleAttrRef("item")[i]``.

Both paths are covered: ``run`` (sync) for every member, ``arun`` (async) for a
representative spread including the higher-order and combinatoric atoms.
"""

from __future__ import annotations

import asyncio
import itertools as pit
import operator

from nu import AnyAttrRef
from nu.context import TupleAttrRef
from nu.core import CollectQuery
from nu.lang.helpers import arun, run
from nu.std.itertools import (
    accumulate,
    batched,
    chain,
    chain_from_iterable,
    combinations,
    combinations_with_replacement,
    compress,
    count,
    cycle,
    dropwhile,
    filterfalse,
    groupby,
    islice,
    pairwise,
    permutations,
    product,
    repeat,
    starmap,
    takewhile,
    tee,
    zip_longest,
)


def mat(form: object) -> list:
    """Materialize an iterator Form to a list via the sync engine path."""
    value, _ = run(CollectQuery(form._children[0]))  # type: ignore[attr-defined]
    return value


async def amat(form: object) -> list:
    """Materialize an iterator Form to a list via the async engine path."""
    value, _ = await arun(CollectQuery(form._children[0]))  # type: ignore[attr-defined]
    return value


# --- infinite sources -------------------------------------------------------


def test_count() -> None:
    assert mat(islice(count(), 5)) == list(pit.islice(pit.count(), 5))


def test_count_start_step() -> None:
    assert mat(islice(count(10, 3), 4)) == list(pit.islice(pit.count(10, 3), 4))


def test_cycle() -> None:
    assert mat(islice(cycle([1, 2, 3]), 7)) == list(pit.islice(pit.cycle([1, 2, 3]), 7))


def test_repeat_times() -> None:
    assert mat(repeat(9, 4)) == list(pit.repeat(9, 4))


def test_repeat_infinite_bounded() -> None:
    assert mat(islice(repeat("x"), 3)) == list(pit.islice(pit.repeat("x"), 3))


# --- pure combinators -------------------------------------------------------


def test_chain() -> None:
    assert mat(chain([1, 2], [3, 4], [5])) == list(pit.chain([1, 2], [3, 4], [5]))


def test_chain_empty() -> None:
    assert mat(chain()) == list(pit.chain())


def test_chain_from_iterable() -> None:
    src = [[1, 2], [3], [4, 5]]
    assert mat(chain_from_iterable(src)) == list(pit.chain.from_iterable(src))


def test_islice_stop() -> None:
    assert mat(islice(range(10), 4)) == list(pit.islice(range(10), 4))


def test_islice_start_stop() -> None:
    assert mat(islice(range(10), 2, 6)) == list(pit.islice(range(10), 2, 6))


def test_islice_start_stop_step() -> None:
    assert mat(islice(range(20), 1, 15, 3)) == list(pit.islice(range(20), 1, 15, 3))


def test_compress() -> None:
    data, sel = ["a", "b", "c", "d"], [1, 0, 1, 1]
    assert mat(compress(data, sel)) == list(pit.compress(data, sel))


def test_pairwise() -> None:
    assert mat(pairwise([1, 2, 3, 4])) == list(pit.pairwise([1, 2, 3, 4]))


def test_pairwise_short() -> None:
    assert mat(pairwise([1])) == list(pit.pairwise([1]))


def test_batched() -> None:
    assert mat(batched(range(7), 3)) == list(pit.batched(range(7), 3))


def test_zip_longest_default_fill() -> None:
    assert mat(zip_longest([1, 2, 3], ["a"])) == list(pit.zip_longest([1, 2, 3], ["a"]))


def test_zip_longest_fillvalue() -> None:
    got = mat(zip_longest([1, 2, 3], ["a"], fillvalue=0))
    assert got == list(pit.zip_longest([1, 2, 3], ["a"], fillvalue=0))


def test_product() -> None:
    assert mat(product([1, 2], ["a", "b"])) == list(pit.product([1, 2], ["a", "b"]))


def test_product_repeat() -> None:
    assert mat(product([0, 1], repeat=3)) == list(pit.product([0, 1], repeat=3))


def test_permutations_full() -> None:
    assert mat(permutations([1, 2, 3])) == list(pit.permutations([1, 2, 3]))


def test_permutations_r() -> None:
    assert mat(permutations([1, 2, 3, 4], 2)) == list(pit.permutations([1, 2, 3, 4], 2))


def test_combinations() -> None:
    assert mat(combinations([1, 2, 3, 4], 2)) == list(pit.combinations([1, 2, 3, 4], 2))


def test_combinations_with_replacement() -> None:
    got = mat(combinations_with_replacement([1, 2, 3], 2))
    assert got == list(pit.combinations_with_replacement([1, 2, 3], 2))


# --- higher-order -----------------------------------------------------------


def test_takewhile() -> None:
    src = [1, 2, 3, 8, 1, 2]
    got = mat(takewhile(AnyAttrRef("item") < 4, src))
    assert got == list(pit.takewhile(lambda x: x < 4, src))


def test_takewhile_first_false() -> None:
    got = mat(takewhile(AnyAttrRef("item") < 4, [9, 1, 2]))
    assert got == list(pit.takewhile(lambda x: x < 4, [9, 1, 2]))


def test_dropwhile() -> None:
    src = [1, 2, 3, 8, 1, 2]
    got = mat(dropwhile(AnyAttrRef("item") < 4, src))
    assert got == list(pit.dropwhile(lambda x: x < 4, src))


def test_dropwhile_all_dropped() -> None:
    got = mat(dropwhile(AnyAttrRef("item") < 100, [1, 2, 3]))
    assert got == list(pit.dropwhile(lambda x: x < 100, [1, 2, 3]))


def test_filterfalse() -> None:
    src = [1, 2, 3, 4, 5, 6]
    got = mat(filterfalse(AnyAttrRef("item") % 2, src))
    assert got == list(pit.filterfalse(lambda x: x % 2, src))


def test_accumulate_default_sum() -> None:
    assert mat(accumulate([1, 2, 3, 4, 5])) == list(pit.accumulate([1, 2, 3, 4, 5]))


def test_accumulate_with_func_sum() -> None:
    src = [1, 2, 3, 4]
    got = mat(accumulate(src, AnyAttrRef("acc") + AnyAttrRef("item")))
    assert got == list(pit.accumulate(src, operator.add))


def test_accumulate_with_func_product() -> None:
    src = [1, 2, 3, 4]
    got = mat(accumulate(src, AnyAttrRef("acc") * AnyAttrRef("item")))
    assert got == list(pit.accumulate(src, operator.mul))


def test_accumulate_single() -> None:
    assert mat(accumulate([42])) == list(pit.accumulate([42]))


def test_starmap() -> None:
    src = [(1, 2), (3, 4), (5, 6)]
    got = mat(starmap(TupleAttrRef("item")[0] + TupleAttrRef("item")[1], src))
    assert got == list(pit.starmap(operator.add, src))


def test_starmap_mul() -> None:
    src = [(2, 3), (4, 5)]
    got = mat(starmap(TupleAttrRef("item")[0] * TupleAttrRef("item")[1], src))
    assert got == list(pit.starmap(operator.mul, src))


def test_groupby_identity() -> None:
    src = [1, 1, 2, 3, 3, 3, 1]
    got = mat(groupby(src))
    assert got == [(k, tuple(g)) for k, g in pit.groupby(src)]


def test_groupby_key() -> None:
    src = [1, 3, 5, 2, 4, 7]
    got = mat(groupby(src, AnyAttrRef("item") % 2))
    assert got == [(k, tuple(g)) for k, g in pit.groupby(src, lambda x: x % 2)]


# --- tee (ScalarQuery returning a tuple of iterators) -----------------------


def test_tee_default() -> None:
    value, _ = run(tee([1, 2, 3]))
    assert [list(it) for it in value] == [list(it) for it in pit.tee([1, 2, 3])]


def test_tee_n() -> None:
    value, _ = run(tee([1, 2, 3, 4], 3))
    assert [list(it) for it in value] == [list(it) for it in pit.tee([1, 2, 3, 4], 3)]


# --- async path -------------------------------------------------------------


def test_async_chain() -> None:
    got = asyncio.run(amat(chain([1, 2], [3, 4])))
    assert got == list(pit.chain([1, 2], [3, 4]))


def test_async_count_islice() -> None:
    got = asyncio.run(amat(islice(count(5, 2), 4)))
    assert got == list(pit.islice(pit.count(5, 2), 4))


def test_async_cycle() -> None:
    got = asyncio.run(amat(islice(cycle([1, 2]), 5)))
    assert got == list(pit.islice(pit.cycle([1, 2]), 5))


def test_async_product() -> None:
    got = asyncio.run(amat(product([1, 2], ["a", "b"])))
    assert got == list(pit.product([1, 2], ["a", "b"]))


def test_async_combinations() -> None:
    got = asyncio.run(amat(combinations([1, 2, 3, 4], 2)))
    assert got == list(pit.combinations([1, 2, 3, 4], 2))


def test_async_zip_longest() -> None:
    got = asyncio.run(amat(zip_longest([1, 2, 3], ["a"], fillvalue=-1)))
    assert got == list(pit.zip_longest([1, 2, 3], ["a"], fillvalue=-1))


def test_async_takewhile() -> None:
    src = [1, 2, 3, 9, 1]
    got = asyncio.run(amat(takewhile(AnyAttrRef("item") < 4, src)))
    assert got == list(pit.takewhile(lambda x: x < 4, src))


def test_async_accumulate_func() -> None:
    src = [1, 2, 3, 4]
    got = asyncio.run(amat(accumulate(src, AnyAttrRef("acc") + AnyAttrRef("item"))))
    assert got == list(pit.accumulate(src, operator.add))


def test_async_starmap() -> None:
    src = [(1, 2), (3, 4)]
    got = asyncio.run(amat(starmap(TupleAttrRef("item")[0] + TupleAttrRef("item")[1], src)))
    assert got == list(pit.starmap(operator.add, src))


def test_async_groupby() -> None:
    src = [1, 1, 2, 2, 3]
    got = asyncio.run(amat(groupby(src)))
    assert got == [(k, tuple(g)) for k, g in pit.groupby(src)]


def test_async_tee() -> None:
    value, _ = asyncio.run(arun(tee([1, 2, 3], 2)))
    assert [list(it) for it in value] == [list(it) for it in pit.tee([1, 2, 3], 2)]
