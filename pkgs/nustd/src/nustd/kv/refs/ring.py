"""kv ring: a capped log of whole entries, the oldest dropping past capacity.

A ring slot keeps the last ``capacity`` entries written to it, oldest first.
Each entry is stored whole, as one row (``[ts, stream, text]`` stays a list),
and has no address of its own: a ring is appended to and read in order, never
written at a position. Built for output a run writes as it goes.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Generic

from typing_extensions import TypeVar

from nu.domains.shape import Slot
from nu.domains.shape.collection import ReactiveCollectionForm, holding
from nu.lang.typeinfo import TypeInfo
from virtuals.views import RingView

from .base import ViewRef, _refuse_container_value


if TYPE_CHECKING:
    from nu.core.reactive import OnChange
    from nu.forms import Int, Iterator, List
    from nu.lang import Arg, IntArg, Nu


__all__ = [
    "RingRef",
]


T = TypeVar("T")
E = TypeVar("E")


class RingRef(ReactiveCollectionForm, ViewRef[list[T]], Generic[T]):
    """A capped log in KV storage: appends land at the end, the oldest drop.

    Notes:
        - Every entry is one row holding the whole value, so a compound
          entry is never decomposed and reads back as written.
        - Appending reads the newest row, writes the entry and drops what
          falls past capacity: a constant number of keys, no stored length
          and no key shared with any other container.
        - Entries have no addresses: there is no ``ring[i]``, no set at a
          position, no per-entry watch. Read with ``iter``, ``reversed``,
          ``len`` or a page of ``entries``.
        - Each entry carries a sequence number that only grows. A reader
          keeps the last one it saw and reads ``entries(after=seq)`` to
          follow the ring; one that fell behind resumes at the oldest entry
          still kept.
        - Meant for one writer, such as a run writing its own output: two
          writers appending at once can pick the same sequence number.
        - A never-written ring raises on ``len`` and iteration, as other
          containers do; ``entries`` reads an empty page there.

    Example:
        class CellRun(Shape):
            out = RingRef.slot(list, capacity=1000)
        run(CellRun.out.append(["12:00", "stdout", "ready"]), ctx)
        run(CellRun.out.entries(after=41, limit=100), ctx)
    """

    extract = ViewRef.extract  # NULL on a never-written container, not core Extract

    _default_view = RingView

    @classmethod
    def slot(
        cls,
        value: type[E],
        *,
        capacity: int | None = None,
        view: type[RingView] | None = None,
    ) -> RingRef[E]:
        """Declare a ring slot keeping the last ``capacity`` entries of ``value``.

        Args:
            value: what each entry is, stored whole: a Python type such as
                ``str`` or ``list``.
            capacity: the most entries kept. Pass this or ``view``.
            view: a ring View class with its capacity, ``RingView.of(n)``.

        Raises:
            TypeError: neither or both of ``capacity`` and ``view`` given, a
                ``view`` without a capacity, or ``value`` a container ref.
            ValueError: ``capacity`` is not an int of at least 1.
        """
        _refuse_container_value(cls, value)
        if (capacity is None) == (view is None):
            msg = "RingRef.slot needs its capacity: pass capacity=n or view=RingView.of(n)"
            raise TypeError(msg)
        if capacity is not None:
            view = RingView.of(capacity)
        elif getattr(view, "CAPACITY", None) is None:
            msg = (
                f"RingRef.slot(view={view.__name__}): a ring view needs a capacity, RingView.of(n)"
            )
            raise TypeError(msg)
        declared = TypeInfo.from_annotation(cls[value])  # type: ignore[index]
        return Slot(cls, type_info=declared, view_type=view)  # type: ignore[return-value]

    @classmethod
    def _slot_kwargs_from_type_args(cls, args: tuple) -> dict[str, object]:
        """An annotation (``out: RingRef[list]``) cannot carry a capacity, so it is refused."""
        msg = "a ring needs its capacity: declare it with RingRef.slot(value, capacity=n)"
        raise TypeError(msg)

    def append(self, entry: Arg[T]) -> Nu:
        """Add ``entry`` as the newest; the oldest drops past capacity.

        Yields:
            Nothing (Command).
        """
        from nu.forms.collections.abc.sequence_interactions import Append

        return Append(self, entry)

    def extend(self, entries: Arg[list[T]]) -> Nu:
        """Append every entry in order, then drop what falls past capacity, once.

        Yields:
            Nothing (Command).
        """
        from nu.forms.collections.abc.sequence_interactions import Extend

        return Extend(self, entries)

    def iter(self) -> Iterator[T]:
        """A lazy stream over the entries kept, oldest first."""
        from nu.core import Iter

        return self._entries_stream(Iter(self))

    def reversed(self) -> Iterator[T]:
        """A lazy stream over the entries kept, newest first."""
        from nu.core import Reversed

        return self._entries_stream(Reversed(self))

    def len(self) -> Int:
        """How many entries are kept. Two seeks, whatever the capacity."""
        from nu.core import Len
        from nu.forms.primitives import Int

        return Int(Len(self))

    def entries(self, *, after: IntArg | None = None, limit: IntArg | None = None) -> List:
        """One page of ``(seq, entry)`` pairs, oldest first, past sequence number ``after``.

        Args:
            after: the sequence number to read past. None starts at the
                oldest entry kept. It need not be kept any
                more: the page starts at the oldest entry still there.
            limit: the most entries to read. None reads to the newest.

        Notes:
            - One seek plus one row per entry: cost tracks ``limit``.
            - A never-written ring reads an empty page.

        Yields:
            A list of ``(seq, entry)`` pairs.

        Example:
            run(CellRun.out.entries(after=41, limit=100), ctx)
        """
        from nu.forms import List
        from nustd.kv.interactions.ring import RingEntries

        return List(RingEntries(self, after, limit))

    def on_change(self) -> OnChange:
        """Observe any entry appended or dropped."""
        from nu.core.reactive import OnChange

        return OnChange(self)

    def _entries_stream(self, operand: Nu) -> Iterator[T]:
        from collections.abc import Iterator as PyIterator

        from nu.forms import Iterator

        return holding(Iterator(operand), PyIterator, elem=self._declared.elem)
