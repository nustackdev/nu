"""kv ring: a capped log of whole entries, the oldest dropping past capacity.

A ring slot keeps the last ``capacity`` entries written to it, oldest first.
Each entry is stored whole, as one row (``[ts, stream, text]`` stays a list),
and has no address of its own. It reads as a Python ``Sequence``, positions
0..len-1 from the oldest kept, and is written only by appending: built for
output a run writes as it goes.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Generic, cast, overload

from typing_extensions import TypeVar

from nu.domains.shape import ReactiveCollectionForm, SequenceRef, Slot
from nu.lang.typeinfo import TypeInfo
from virtuals.views import RingView

from .base import ViewRef, _refuse_container_value


if TYPE_CHECKING:
    from collections.abc import Iterable

    from nu.core.reactive import OnChange
    from nu.forms import Iterator, List, Object
    from nu.lang import Arg, IntArg, Nu


__all__ = [
    "RingRef",
]


T = TypeVar("T")
E = TypeVar("E")


class RingRef(SequenceRef, ReactiveCollectionForm, ViewRef[list[T]], Generic[T]):
    """A capped log in KV storage: appends land at the end, the oldest drop.

    A read-only Python ``Sequence`` plus ``append``, ``extend`` and
    ``clear``, as an ordered dict slot is a mapping plus placement.

    Notes:
        - Every entry is one row holding the whole value, so a compound
          entry is never decomposed and reads back as written.
        - Reads are the sequence ones: ``ring[i]``, slices, ``iter``,
          ``reversed``, ``len``, ``contains``, ``index``, ``count``,
          ``first_elem``, ``last_elem``. Position 0 is the oldest entry
          kept, -1 the newest, so a position names a different entry once
          the ring drops one.
        - ``ring[i]`` reads the entry, it is not a ref: entries have no
          addresses, so there is no write at a position and no per-entry
          watch. An index past the ends raises IndexError.
        - Appending reads the newest row, writes the entry and drops what
          falls past capacity: a constant number of keys, no stored length
          and no key shared with any other container.
        - Meant for one writer, such as a run writing its own output: two
          writers appending at once can collide.
        - A never-written ring raises on ``len``, iteration and reads by
          position, as other containers do; ``extract()`` gives NULL.

    Example:
        class CellRun(Shape):
            out = RingRef.slot(list, capacity=1000)
        run(CellRun.out.append(["12:00", "stdout", "ready"]), ctx)
        run(CellRun.out[-100:], ctx)
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
                ``view`` that is not a ring or has no capacity, or ``value``
                a container ref.
            ValueError: ``capacity`` is not an int of at least 1.
        """
        _refuse_container_value(cls, value)
        if (capacity is None) == (view is None):
            msg = "RingRef.slot needs its capacity: pass capacity=n or view=RingView.of(n)"
            raise TypeError(msg)
        if capacity is not None:
            view = RingView.of(capacity)
        elif not (isinstance(view, type) and issubclass(view, RingView)):
            msg = f"RingRef.slot(view={view!r}): the view must be a ring with a capacity, RingView.of(n)"
            raise TypeError(msg)
        elif view.CAPACITY is None:
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

    # an entry has no address of its own, so ``ring[i]`` reads it instead of descending
    @overload  # type: ignore[override]
    def __getitem__(self, index: IntArg) -> Object: ...
    @overload
    def __getitem__(self, index: slice) -> List[T]: ...
    def __getitem__(self, index: IntArg | slice) -> Object | List[T]:
        """The entry at ``index``, oldest first, read whole; a slice is a List.

        Notes:
            - A read, not a child ref: an entry has no address of its own,
              so this skips the child navigation ``SequenceRef`` gives.
        """
        # the value form's subscript, past SequenceRef's descent
        return cast("Object | List[T]", super(SequenceRef, self).__getitem__(index))

    def iter(self) -> Iterator[T]:
        """A lazy stream over the entries kept, oldest first."""
        return super().iter()

    def append(self, entry: Arg[T]) -> Nu:
        """Add ``entry`` as the newest; the oldest drops past capacity.

        Yields:
            Nothing (Command).
        """
        from nu.forms.collections.abc.sequence_interactions import Append

        return Append(self, entry)

    def extend(self, entries: Arg[Iterable[T]]) -> Nu:
        """Append every entry in order, then drop what falls past capacity, once.

        Yields:
            Nothing (Command).
        """
        from nu.forms.collections.abc.sequence_interactions import Extend

        return Extend(self, entries)

    def clear(self) -> Nu:
        """Drop every entry. The ring stays, empty, and numbering goes on.

        Yields:
            Nothing (Command).
        """
        from nu.forms.collections.abc.shared_interactions import Clear

        return Clear(self)

    def on_change(self) -> OnChange:
        """Observe any entry appended or dropped."""
        from nu.core.reactive import OnChange

        return OnChange(self)
