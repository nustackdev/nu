"""kh57 atoms: read a sub-range of an int-keyed series, sampled or whole.

A ``Kh57Ref`` names a container whose keys are integers spread across levels,
built so that a uniform sample of any sub-range costs about the same whether
the range holds a thousand entries or a billion. These two atoms are the read
side of that: one draws a bounded sample, the other materializes everything.

Both take the container Ref at slot 0 and their bounds as ordinary children,
so a bound can be another Ref read at run time rather than a number fixed when
the tree was written. Both come back as a list of ``(int_key, value)`` pairs
and both answer EMPTY when the container is not reachable.

Neither is written directly in normal use. ``Kh57Ref.sample`` and
``Kh57Ref.range`` build them, already wrapped in the ``Any`` form.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from nu.lang import ScalarQuery
from nu.lang.sentinels import EMPTY


if TYPE_CHECKING:
    import random
    from collections.abc import Callable

    from nu.lang import IntArg, Nu
    from nu.lang.runtime import Runtime


__all__ = [
    "Kh57Range",
    "Kh57Sample",
]


def _child_nid(rt: Runtime, nid: int, slot: int) -> int:
    return rt.program.children[nid][slot]


class Kh57Sample(ScalarQuery):
    """Draws a uniform sample of a kh57 series' sub-range, in bounded time.

    Cost tracks ``n`` rather than the size of the range, so sampling a window
    holding a billion entries is no dearer than one holding a thousand. That
    is what makes it usable as the read behind a live chart over a series that
    keeps growing.

    Args:
        ref: the kh57 container Ref to sample.
        n: the ceiling on how many pairs come back. A range holding fewer
            than ``n`` entries yields all of them.
        begin: inclusive lower bound on the int key. None leaves the range
            open at the bottom.
        end: exclusive upper bound on the int key. None leaves the range
            open at the top.

    Notes:
        - ``n``, ``begin`` and ``end`` are children, so each may be a Ref
          read at run time; a raw value is wrapped as a Literal.
        - The keyword-only ``rng`` picks the random source; seed it to make
          a run reproducible. It is not a child: it rides the atom's
          payload, so a tree rewrite carries it, but it cannot be computed.
        - The sample is stable under appends outside the queried range: rows
          landing above ``end`` do not disturb what a fixed window returns.
        - Bounds are evaluated after the container is opened, so a missing
          container short-circuits before they run.

    Yields:
        A list of ``(int_key, value)`` pairs, unordered. EMPTY when the
        container is not reachable.

    Example:
        class State(nu.Shape):
            nums = nu.kv.Kh57Ref.slot(int)
            cursor = nu.kv.IntRef.slot()

        app = nu.With(
            nu.kv.memory_navigator(),
            body=nu.kv.Snapshot(Kh57Sample(State.nums, 200, 0, State.cursor)),
        )
    """

    def __init__(
        self,
        ref: Nu,
        n: IntArg,
        begin: IntArg | None = None,
        end: IntArg | None = None,
        *,
        rng: random.Random | None = None,
    ) -> None:
        super().__init__(ref, n, begin, end)
        # rng rides in _payload so Term._with_children (which shares payload
        # across a tree rewrite) carries it. Storing on __dict__ would lose
        # it on the first auto_flow_atomic pass.
        self._payload["rng"] = rng

    def _compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        ref = self._children[0]
        _ref_thunk, n_thunk, begin_thunk, end_thunk = children
        rng = self._payload.get("rng")

        def thunk(rt: Runtime) -> object:
            try:
                view = ref._fetch(rt, _child_nid(rt, nid, 0))
            except (KeyError, IndexError):
                return EMPTY
            n = n_thunk(rt)
            begin = begin_thunk(rt)
            end = end_thunk(rt)
            return view.sample(n, begin, end, rng=rng)

        return thunk

    def _acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        ref = self._children[0]
        _ref_thunk, n_thunk, begin_thunk, end_thunk = children
        rng = self._payload.get("rng")

        async def athunk(rt: Runtime) -> object:
            try:
                view = await ref._afetch(rt, _child_nid(rt, nid, 0))
            except (KeyError, IndexError):
                return EMPTY
            n = await n_thunk(rt)
            begin = await begin_thunk(rt)
            end = await end_thunk(rt)
            return view.sample(n, begin, end, rng=rng)

        return athunk


class Kh57Range(ScalarQuery):
    """Reads a kh57 series' sub-range whole, in ascending key order.

    The keys of a kh57 container are spread across levels, so a range is
    assembled by merging one ordered walk per level. Cost tracks the size of
    the range, unlike ``Kh57Sample``: this is the atom for a window you know
    is small, and the wrong one for a window that grows without bound.

    The merged walk is drained into a list before the value leaves the atom,
    to match ``Kh57Sample``'s scalar shape. Anyone wanting to stream iterates
    the list.

    Args:
        ref: the kh57 container Ref to read.
        begin: inclusive lower bound on the int key. Must be non-negative.
        end: exclusive upper bound on the int key. Must not exceed the key
            space the container's level layout covers.

    Notes:
        - ``begin`` and ``end`` are children, so either may be a Ref read at
          run time; a raw value is wrapped as a Literal.
        - Unlike ``Kh57Sample`` the bounds are required, not optional: there
          is no open-ended form.
        - An empty or inverted range (``begin >= end``) yields an empty list
          rather than an error. Out-of-space bounds do raise ``ValueError``.
        - Bounds are evaluated after the container is opened, so a missing
          container short-circuits before they run.

    Yields:
        A list of ``(int_key, value)`` pairs with ``begin <= int_key < end``,
        ascending by key. EMPTY when the container is not reachable.

    Example:
        app = nu.With(
            nu.kv.memory_navigator(),
            body=nu.kv.Snapshot(Kh57Range(State.nums, 0, 100)),
        )
    """

    def _compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        ref = self._children[0]
        _ref_thunk, begin_thunk, end_thunk = children

        def thunk(rt: Runtime) -> object:
            try:
                view = ref._fetch(rt, _child_nid(rt, nid, 0))
            except (KeyError, IndexError):
                return EMPTY
            begin = begin_thunk(rt)
            end = end_thunk(rt)
            return list(view.range(begin, end))

        return thunk

    def _acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        ref = self._children[0]
        _ref_thunk, begin_thunk, end_thunk = children

        async def athunk(rt: Runtime) -> object:
            try:
                view = await ref._afetch(rt, _child_nid(rt, nid, 0))
            except (KeyError, IndexError):
                return EMPTY
            begin = await begin_thunk(rt)
            end = await end_thunk(rt)
            return list(view.range(begin, end))

        return athunk
