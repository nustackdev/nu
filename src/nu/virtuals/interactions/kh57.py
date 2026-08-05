"""Virtuals kh57 interactions: range reservoir sampling atoms.

Kh57Sample: scalar query, yields a list of ``(int_key, value)`` samples
from a Kh57View's sub-range via ``kh57.sample`` (range reservoir sampling).

Kh57Range: stream query, yields ``(int_key, value)`` pairs from a
Kh57View's sub-range in original int-key order.

Both hold the container view Ref at ``children[0]``; parameters (n, begin,
end) live at slots 1..3 and are auto-wrapped as Literal when passed as
raw values. Both are deterministic: same view state + same seeded rng
gives the same result.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from nu.lang import ScalarQuery
from nu.lang.sentinels import EMPTY


if TYPE_CHECKING:
    import random
    from collections.abc import Callable

    from nu.lang import Nu
    from nu.lang.runtime import Runtime


__all__ = [
    "Kh57Range",
    "Kh57Sample",
]


def _child_nid(rt: Runtime, nid: int, slot: int) -> int:
    return rt.program.children[nid][slot]


class Kh57Sample(ScalarQuery):
    """Range reservoir sample from a Kh57View.

    Yields a list of ``(int_key, value)`` pairs from the sub-range
    ``[begin, end)``. Deterministic given the view's salt + a seeded ``rng``.
    Stable under appends outside the queried range.

    Children:
        0: kh57 view Ref
        1: n, number of samples requested
        2: begin, inclusive lower bound (None means unbounded)
        3: end, exclusive upper bound (None means unbounded)
    """

    def __init__(
        self,
        ref: Nu,
        n: int | Nu,
        begin: int | Nu | None = None,
        end: int | Nu | None = None,
        *,
        rng: random.Random | None = None,
    ) -> None:
        super().__init__(ref, n, begin, end)
        # rng rides in _payload so Term._with_children (which shares payload
        # across a tree rewrite) carries it. Storing on __dict__ would lose
        # it on the first inline_refs / auto_flow_atomic pass.
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
    """Ordered materialization of a Kh57View sub-range.

    Yields a list of ``(int_key, value)`` pairs with ``begin <= int_key < end``,
    in ascending int-key order. Level-merged under the hood. Materialized to
    a list to match ``.sample()``'s scalar shape; users who want to stream
    can iterate the returned list.

    Children:
        0: kh57 view Ref
        1: begin, inclusive lower bound
        2: end, exclusive upper bound
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
