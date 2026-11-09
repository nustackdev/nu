"""Ring reads: one page of a ring's entries past a sequence number.

``RingRef.entries(after=, limit=)`` builds the atom; it is not written
directly in normal use.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from nu.forms.collections.abc.mapping_interactions import _page_args
from nu.lang import ScalarQuery


if TYPE_CHECKING:
    from collections.abc import Callable

    from nu.lang.runtime import Runtime


__all__ = [
    "RingEntries",
]


class RingEntries(ScalarQuery):
    """Reads a page of a ring's entries, oldest first, past a sequence number.

    Args:
        ref: the ring Ref to read.
        after: the sequence number to read past, or None for the oldest
            entry kept.
        limit: the most entries to read, or None to read to the newest.

    Notes:
        - One seek, then one row per entry: cost tracks ``limit``.
        - ``after`` need not be kept any more: the page starts at the oldest
          entry still there.
        - ``after`` or ``limit`` reading NULL raises ``ValueError`` before the
          view is called; None reads from the oldest or to the newest.
        - The ring view checks the args and raises on a never-written ring,
          as ``len`` and iteration do.
        - The page is read whole before it leaves the atom, so it outlives
          the bracket it was read in.

    Yields:
        A list of ``(seq, entry)`` pairs.
    """

    def _compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        ref_thunk, after_thunk, limit_thunk = children

        def thunk(rt: Runtime) -> object:
            view = ref_thunk(rt)
            after, limit = _page_args("entries", "after", after_thunk(rt), limit_thunk(rt))
            return list(view.entries(after=after, limit=limit))

        return thunk

    def _acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        ref_thunk, after_thunk, limit_thunk = children

        async def athunk(rt: Runtime) -> object:
            view = await ref_thunk(rt)
            after, limit = _page_args(
                "entries", "after", await after_thunk(rt), await limit_thunk(rt)
            )
            return list(view.entries(after=after, limit=limit))

        return athunk
