"""Ring reads: one page of a ring's entries past a sequence number.

``RingRef.entries(after=, limit=)`` builds the atom; it is not written
directly in normal use.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from nu.lang import ScalarQuery
from nu.lang.null import Null, is_null
from nustd.kv.interactions.paging import _check_limit
from nustd.kv.refs.base import _null_at
from virtuals.container import ContainerNotFoundError


if TYPE_CHECKING:
    from collections.abc import Callable

    from nu.lang.runtime import Runtime


__all__ = [
    "RingEntries",
]


def _entries(ref: object, rt: Runtime, path: tuple, after: object, limit: object) -> object:
    """``(seq, entry)`` pairs past ``after``, at most ``limit``, as a list."""
    limit = _check_limit(limit)
    if _null_at(path):
        return Null(ref._hint(path))  # type: ignore[attr-defined]
    if is_null(after):
        after = None
    if after is not None and (isinstance(after, bool) or not isinstance(after, int)):
        raise TypeError(f"a ring cursor is a sequence number, got {after!r}")
    view = ref._open(rt, path)  # type: ignore[attr-defined]
    try:
        return list(view.entries(after=after, limit=limit))
    except ContainerNotFoundError:
        return []


class RingEntries(ScalarQuery):
    """Reads a page of a ring's entries, oldest first, past a sequence number.

    Args:
        ref: the ring Ref to read.
        after: the sequence number to read past, or None (or NULL) for the
            oldest entry kept.
        limit: the most entries to read, or None to read to the newest.

    Notes:
        - One seek, then one row per entry: cost tracks ``limit``.
        - ``after`` need not be kept any more: the page starts at the oldest
          entry still there.
        - A never-written ring reads an empty page. A path with a key that
          read NULL reads NULL.
        - The page is read whole before it leaves the atom, so it outlives
          the bracket it was read in.

    Yields:
        A list of ``(seq, entry)`` pairs.
    """

    def _compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        ref = self._children[0]
        _ref_thunk, after_thunk, limit_thunk = children

        def thunk(rt: Runtime) -> object:
            path = ref._resolve_path(rt, rt.program.children[nid][0])
            return _entries(ref, rt, path, after_thunk(rt), limit_thunk(rt))

        return thunk

    def _acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        ref = self._children[0]
        _ref_thunk, after_thunk, limit_thunk = children

        async def athunk(rt: Runtime) -> object:
            path = await ref._aresolve_path(rt, rt.program.children[nid][0])
            after, limit = await after_thunk(rt), await limit_thunk(rt)
            return _entries(ref, rt, path, after, limit)

        return athunk
