"""Paged key reads: one bounded page of a mapping's keys, and its two ends.

A big collection is never read whole. These atoms read a page of keys from a
cursor, or the key at one end, each from one seek into storage, so the cost
tracks the page and not the collection. They work on the views that keep an
order they can seek in: ``DictView`` (key order), ``FractionalIndexedDictView``
(placed order) and ``LogIndexedDictView`` (the order ids were first set).

Every atom takes the container Ref at slot 0 and its cursor and limit as
ordinary children, so a cursor can be a ref read at run time, such as the last
key of the page shown before.

None is written directly in normal use. ``keys(after=, limit=)`` and
``reversed_keys(before=, limit=)`` on a mapping ref build the page atoms;
``LogDictRef.first`` and ``last`` build the end atoms.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from nu.lang import ScalarQuery
from nu.lang.null import Null, is_null
from nustd.kv.refs.base import _null_at
from virtuals.container import ContainerNotFoundError


if TYPE_CHECKING:
    from collections.abc import Callable

    from nu.lang.runtime import Runtime


__all__ = [
    "FirstKey",
    "KeysPage",
    "LastKey",
    "ReversedKeysPage",
]


def _child_nid(rt: Runtime, nid: int, slot: int) -> int:
    return rt.program.children[nid][slot]


def _pages(view_type: object) -> bool:
    """Whether a View class reads its keys a page at a time."""
    return callable(getattr(view_type, "keys_reverse", None))


def _check_limit(limit: object) -> int | None:
    if limit is None:
        return None
    if is_null(limit):
        raise ValueError("limit read NULL: pass a count, or None to read to the end")
    if isinstance(limit, bool) or not isinstance(limit, int) or limit < 0:
        raise ValueError(f"limit must be a count of zero or more, got {limit!r}")
    return limit


def _page(
    ref: object, rt: Runtime, path: tuple, cursor: object, limit: object, reverse: bool
) -> object:
    """Keys past ``cursor`` (before it when ``reverse``), at most ``limit``, as a list."""
    limit = _check_limit(limit)
    if _null_at(path):
        return Null(ref._hint(path))  # type: ignore[attr-defined]
    if is_null(cursor):
        cursor = None
    view = ref._open(rt, path)  # type: ignore[attr-defined]
    if not _pages(view):
        msg = f"{type(view).__name__} does not page its keys; use a Dict, ordered or log view"
        raise TypeError(msg)
    try:
        if reverse:
            return list(view.keys_reverse(before=cursor, limit=limit))
        return list(view.keys(after=cursor, limit=limit))
    except ContainerNotFoundError:
        return []
    except KeyError as missing:
        where = ref._hint(path)  # type: ignore[attr-defined]
        raise KeyError(f"{where}: no {cursor!r} to page from") from missing


def _end(ref: object, rt: Runtime, path: tuple, last: bool) -> object:
    """The key at one end of the order; NULL when nothing is there, written or not."""
    found = _page(ref, rt, path, None, 1, last)
    return found[0] if found else Null(ref._hint(path))  # type: ignore[index, attr-defined]


class _PageBase(ScalarQuery):
    """Shared base: open the view and read one page. Children are ``(ref, cursor, limit)``."""

    _reverse: bool = False

    def _compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        ref = self._children[0]
        _ref_thunk, cursor_thunk, limit_thunk = children
        reverse = self._reverse

        def thunk(rt: Runtime) -> object:
            path = ref._resolve_path(rt, _child_nid(rt, nid, 0))
            return _page(ref, rt, path, cursor_thunk(rt), limit_thunk(rt), reverse)

        return thunk

    def _acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        ref = self._children[0]
        _ref_thunk, cursor_thunk, limit_thunk = children
        reverse = self._reverse

        async def athunk(rt: Runtime) -> object:
            path = await ref._aresolve_path(rt, _child_nid(rt, nid, 0))
            cursor, limit = await cursor_thunk(rt), await limit_thunk(rt)
            return _page(ref, rt, path, cursor, limit, reverse)

        return athunk


class KeysPage(_PageBase):
    """Reads a page of keys in the collection's order, starting past a cursor.

    Args:
        ref: the mapping Ref to read.
        after: the key to start past, or None (or NULL) for the first page.
        limit: the most keys to read, or None to read to the end.

    Notes:
        - One seek, then one row per key: cost tracks ``limit``, never the
          size of the collection.
        - The order is the view's: key order on a dict, placed order on an
          ordered dict, the order ids were first set on a log.
        - On a dict the cursor is a position, so it need not be there: a
          page resumes past a key deleted since. On an ordered dict or a log
          it is an id the collection holds, and KeyError when it is gone.
        - An empty collection and one never written read an empty page. A
          path with a key that read NULL reads NULL.
        - The page is read whole before it leaves the atom, so it outlives
          the bracket it was read in.

    Yields:
        A list of keys.

    Example:
        app = nu.With(
            nustd.kv.memory_navigator(),
            body=nustd.kv.Snapshot(KeysPage(Space.indexes.removed, None, 20)),
        )
    """

    _reverse = False


class ReversedKeysPage(_PageBase):
    """Reads a page of keys in reverse order, starting before a cursor.

    Same contract as ``KeysPage``, from the other end: on a log the newest
    ids come first.

    Args:
        ref: the mapping Ref to read.
        before: the key to start before, or None (or NULL) for the last page.
        limit: the most keys to read, or None to read to the start.

    Yields:
        A list of keys, last first.
    """

    _reverse = True


class _EndBase(ScalarQuery):
    """Shared base: read the key at one end of the order, in one seek."""

    _last: bool = False

    def _compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        ref = self._children[0]
        last = self._last

        def thunk(rt: Runtime) -> object:
            return _end(ref, rt, ref._resolve_path(rt, _child_nid(rt, nid, 0)), last)

        return thunk

    def _acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        ref = self._children[0]
        last = self._last

        async def athunk(rt: Runtime) -> object:
            return _end(ref, rt, await ref._aresolve_path(rt, _child_nid(rt, nid, 0)), last)

        return athunk


class FirstKey(_EndBase):
    """Reads the first key in the collection's order, in one seek.

    Args:
        ref: the mapping Ref to read.

    Notes:
        - On a log it is the oldest id.
        - NULL on an empty collection, one never written, or one under a key
          that read NULL: a read that finds nothing gives NULL.
        - Safe under a Snapshot: a missing container is never created.

    Yields:
        The first key, or NULL.
    """

    _last = False


class LastKey(_EndBase):
    """Reads the last key in the collection's order, in one seek.

    Same contract as ``FirstKey``, from the other end: on a log it is the
    newest id.

    Args:
        ref: the mapping Ref to read.

    Yields:
        The last key, or NULL.
    """

    _last = True
