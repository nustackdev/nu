"""kv log dict: an append-only mapping, listed in the order its ids were added.

A dict slot laid out as a log: each new id is logged once, when first set, and
the collection lists in that order. Built for lists that only grow and are read
a page at a time, newest first: run history, removed rows, the planes made from
one spec. Everything else, descent and typing included, is a ``DictRef``.
"""

from __future__ import annotations

from typing import Generic

from typing_extensions import TypeVar

from nu.domains.shape import Slot
from nu.forms import Object
from nu.lang.sentinels import UNSET
from nu.lang.typeinfo import TypeInfo
from virtuals.views import LogIndexedDictView, LogIndexedDictViewBase

from .base import _refuse_container_value
from .containers import DictRef, _require_view


__all__ = [
    "LogDictRef",
]


K = TypeVar("K")
V = TypeVar("V")
DK = TypeVar("DK", default=str)
DV = TypeVar("DV")


class LogDictRef(DictRef[K, V], Generic[K, V]):
    """An append-only mapping in KV storage, in the order its ids were added.

    Same mapping surface as a dict slot, with the ids kept in log order:
    iteration, ``keys``, ``values`` and ``items`` come back oldest first, and
    ``reversed_keys`` newest first. Paged with ``keys(after=, limit=)`` and
    ``reversed_keys(before=, limit=)``, followed with ``nu.Stream``.

    Notes:
        - Setting a new id logs it at the end: three rows, no read, so any
          number of writers append without contending on a shared key.
          Setting an existing id keeps its place.
        - Deleting an id is a point op. Nothing moves: there is no insert or
          move.
        - ``len`` scans the whole log, O(n). For the newest ids read
          ``last()`` or ``reversed_keys(limit=)``, one seek each.
        - ``first`` and ``last`` are one seek each: the oldest and the newest
          id.
        - The order is wall-clock time across processes, so two writers in
          the same millisecond land in either order.
        - A page cursor is an id the log holds; a deleted one raises
          KeyError. A stream keeps its own cursor and resumes past it.

    Example:
        class Indexes(Shape):
            removed = LogDictRef.slot(bool)
        run(Indexes.removed.set_item("p1", True), ctx)
        run(Indexes.removed.reversed_keys(limit=20), ctx)
        run(Indexes.removed.last(), ctx)
    """

    _default_view = LogIndexedDictView

    @classmethod
    def slot(  # type: ignore[override]
        cls,
        value: type[DV],
        *,
        key: type[DK] = str,  # type: ignore[assignment]
        view: type[LogIndexedDictViewBase] | None = None,
    ) -> LogDictRef[DK, DV]:
        """Declare an append-only mapping slot holding ``value`` under ``key`` ids.

        Args:
            value: what each id holds: a Python type, a Shape, or a kv leaf
                class.
            key: the id type. Defaults to ``str``.
            view: the View class laying the log out. Defaults to
                ``LogIndexedDictView``.

        Raises:
            TypeError: ``value`` is a container ref. Hold a Shape with that
                container as a slot instead.

        Notes:
            - ``runs: LogDictRef[str, bool]`` as an annotation declares the
              same slot.
        """
        _refuse_container_value(cls, value)
        _require_view(
            cls, view, (LogIndexedDictViewBase,), "a log indexed dict view, as LogIndexedDictView"
        )
        declared = TypeInfo.from_annotation(cls[key, value])  # type: ignore[index]
        return Slot(cls, type_info=declared, view_type=view)  # type: ignore[return-value]

    def first(self, default: object = UNSET) -> Object:
        """Read the oldest id.

        Args:
            default: yielded when there is no oldest id, the log being empty
                or never written, as ``next(iter(d), default)``. Any term,
                NULL included (``nu.NullForm()``). Leave it out to raise
                instead.

        Notes:
            - One seek, whatever the size of the log.
            - Safe under a Snapshot.

        Yields:
            The oldest id, or ``default``. Without a default, IndexError when
            the log is empty and ContainerNotFoundError when it was never
            written.

        Example:
            run(Indexes.removed.first(), ctx)
            run(Indexes.removed.first(default=nu.NullForm()), ctx)
        """
        from nustd.kv.interactions.ordered import OrderedFirst

        return Object(OrderedFirst(self, default))

    def last(self, default: object = UNSET) -> Object:
        """Read the newest id.

        Args:
            default: yielded when there is no newest id. Same contract as
                ``first``.

        Notes:
            - One seek, whatever the size of the log.
            - Safe under a Snapshot.

        Yields:
            The newest id, or ``default``. Without a default, raises as
            ``first`` does.

        Example:
            run(Indexes.removed.last(), ctx)
        """
        from nustd.kv.interactions.ordered import OrderedLast

        return Object(OrderedLast(self, default))
