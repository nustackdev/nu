"""kv ordered dict: a mapping whose ids keep the order they were placed in.

A dict slot whose iteration order is the collection order, with ids placed
next to each other and moved without touching the rest. Everything else,
descent and typing included, is a ``DictRef``.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Generic

from typing_extensions import TypeVar

from nu.domains.shape import Slot
from nu.forms import Object
from nu.lang import Nu
from nu.lang.sentinels import UNSET
from nu.lang.typeinfo import TypeInfo
from virtuals.views import FractionalIndexedDictView, FractionalIndexedDictViewBase

from .base import _refuse_container_value
from .containers import DictRef, _require_view


if TYPE_CHECKING:
    from nu.lang import Arg


__all__ = [
    "OrderedDictRef",
]


K = TypeVar("K")
V = TypeVar("V")
DK = TypeVar("DK", default=str)
DV = TypeVar("DV")


class OrderedDictRef(DictRef[K, V], Generic[K, V]):
    """An ordered mapping in KV storage, laid out so placement is cheap.

    Same mapping surface as a dict slot, with the ids kept in collection
    order: iteration, ``keys``, ``values`` and ``items`` come back in the
    order the ids were placed, not in key order. Built for membership lists
    where an entry sits between two others and gets moved around, such as
    the cells of a plane or the children of a node.

    Notes:
        - Setting a new id appends it; setting an existing id keeps its
          place. Deleting one touches only its own rows.
        - ``insert_before``, ``insert_after`` and ``move`` place an id
          relative to another id, never to an index. Each is one view call,
          and each costs a constant number of storage touches whatever the
          size of the collection.
        - ``first`` and ``last`` are one seek each; nothing stored tracks
          the ends, so writers never contend on a shared head or tail.
        - Two writers placing between the same neighbours never collide:
          their ids land in some stable order next to each other.
        - A value of ``True`` is the idiom for pure membership, where the
          collection is the order and nothing else.

    Example:
        class Plane(Shape):
            cells = OrderedDictRef.slot(bool)
        run(Plane.cells.set_item("c1", True), ctx)
        run(Plane.cells.insert_before("c1", "c0"), ctx)
        run(Plane.cells.move("c1", before="c0"), ctx)
        run(Plane.cells.first(), ctx)
    """

    _default_view = FractionalIndexedDictView

    @classmethod
    def slot(  # type: ignore[override]
        cls,
        value: type[DV],
        *,
        key: type[DK] = str,  # type: ignore[assignment]
        view: type[FractionalIndexedDictViewBase] | None = None,
    ) -> OrderedDictRef[DK, DV]:
        """Declare an ordered mapping slot holding ``value`` under ``key`` ids.

        Args:
            value: what each id holds: a Python type, a Shape, or a kv leaf
                class.
            key: the id type. Defaults to ``str``.
            view: the View class laying the collection out. Defaults to
                ``FractionalIndexedDictView``.

        Notes:
            - ``cells: OrderedDictRef[str, bool]`` as an annotation declares
              the same slot.
            - ``insert_before`` and ``insert_after`` store ``True`` when no
              value is passed, whatever ``value`` declares; pass the value
              explicitly on a slot that is not ``bool``.
        """
        _refuse_container_value(cls, value)
        _require_view(
            cls,
            view,
            (FractionalIndexedDictViewBase,),
            "a fractional indexed dict view, as FractionalIndexedDictView",
        )
        declared = TypeInfo.from_annotation(cls[key, value])  # type: ignore[index]
        return Slot(cls, type_info=declared, view_type=view)  # type: ignore[return-value]

    def insert_before(self, anchor: Arg[K], id: Arg[K], value: Arg[V] = True) -> Any:  # noqa: ANN401
        """Add ``id`` directly before ``anchor``.

        Args:
            anchor: an id already in the collection.
            id: the id to add.
            value: what ``id`` holds. Defaults to ``True``, the membership
                idiom; a plain mapping is decomposed under the id.

        Notes:
            - Raises ValueError when ``id`` is already present or any
              operand reads NULL, and KeyError when ``anchor`` is absent.
            - Each argument is a child, so any of them may be an expression
              or a ref read at run time.
            - One view call, a constant number of storage touches.
            - Mutating Command: mutates slot 0 in place, yields nothing.

        Yields:
            Nothing.

        Example:
            run(Plane.cells.insert_before("c1", "c0"), ctx)
        """
        from nustd.kv.interactions.ordered import OrderedInsertBeforeCmd

        return OrderedInsertBeforeCmd(self, anchor, id, value)

    def insert_after(self, anchor: Arg[K], id: Arg[K], value: Arg[V] = True) -> Any:  # noqa: ANN401
        """Add ``id`` directly after ``anchor``.

        Args:
            anchor: an id already in the collection.
            id: the id to add.
            value: what ``id`` holds. Defaults to ``True``, the membership
                idiom; a plain mapping is decomposed under the id.

        Notes:
            - Raises ValueError when ``id`` is already present or any
              operand reads NULL, and KeyError when ``anchor`` is absent.
            - Each argument is a child, so any of them may be an expression
              or a ref read at run time.
            - One view call, a constant number of storage touches.
            - Mutating Command: mutates slot 0 in place, yields nothing.

        Yields:
            Nothing.

        Example:
            run(Plane.cells.insert_after("c1", "c2"), ctx)
        """
        from nustd.kv.interactions.ordered import OrderedInsertAfterCmd

        return OrderedInsertAfterCmd(self, anchor, id, value)

    def move(
        self,
        id: Arg[K],
        *,
        before: Arg[K] | None = None,
        after: Arg[K] | None = None,
    ) -> Any:  # noqa: ANN401
        """Move ``id`` directly before or after another id.

        Args:
            id: an id already in the collection.
            before: the id to land in front of.
            after: the id to land behind.

        Notes:
            - Exactly one of ``before`` and ``after`` is given; both or
              neither raises ValueError, here when both are plain values and
              at run time when either is an expression. An absent id raises
              KeyError, a NULL one ValueError.
            - The value under ``id`` is untouched; only its place changes.
              Moving an id to where it already is does nothing.
            - Each argument is a child, so any of them may be an expression
              or a ref read at run time.
            - One view call, a constant number of storage touches.
            - Mutating Command: mutates slot 0 in place, yields nothing.

        Yields:
            Nothing.

        Example:
            run(Plane.cells.move("c3", before="c1"), ctx)
            run(Plane.cells.move("c1", after="c3"), ctx)
        """
        from nustd.kv.interactions.ordered import OrderedMoveCmd

        plain = not (isinstance(before, Nu) or isinstance(after, Nu))
        if plain and (before is None) == (after is None):
            raise ValueError("move takes exactly one of before= or after=")
        return OrderedMoveCmd(self, id, before, after)

    def first(self, default: object = UNSET) -> Object:
        """Read the first id in collection order.

        Args:
            default: yielded when there is no first id, the collection being
                empty or never written, as ``next(iter(d), default)``. Any
                term, NULL included (``nu.NullForm()``). Leave it out to
                raise instead.

        Notes:
            - One seek, whatever the size of the collection.
            - Safe under a Snapshot.

        Yields:
            The first id, or ``default``. Without a default, IndexError when
            the collection is empty and ContainerNotFoundError when it was
            never written.

        Example:
            run(Plane.cells.first(), ctx)
            run(Plane.cells.first(default=nu.NullForm()), ctx)
        """
        from nustd.kv.interactions.ordered import OrderedFirst

        return Object(OrderedFirst(self, default))

    def last(self, default: object = UNSET) -> Object:
        """Read the last id in collection order.

        Args:
            default: yielded when there is no last id. Same contract as
                ``first``.

        Notes:
            - One seek, whatever the size of the collection.
            - Safe under a Snapshot.

        Yields:
            The last id, or ``default``. Without a default, raises as
            ``first`` does.

        Example:
            run(Plane.cells.last(), ctx)
        """
        from nustd.kv.interactions.ordered import OrderedLast

        return Object(OrderedLast(self, default))
