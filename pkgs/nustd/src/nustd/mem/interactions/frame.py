"""``Frame``: a private mem store for one scope.

A frame is the stack frame of a Nu program. Whatever a body computes once and
reads again, counts, or accumulates lives in the frame's own dict, laid out by
a Shape, and goes away when the body ends. Nothing about it is new machinery:
the dict is bound under ``(dict, Shape)`` with the scoped ``ctx.fabrics.bind``
every lifecycle bracket uses, and the Shape's mem refs read and write it like
any other mem root.
"""

from __future__ import annotations

from contextlib import contextmanager
from typing import TYPE_CHECKING

from nu.core.spans.bracket import _LifecycleBracket


if TYPE_CHECKING:
    from collections.abc import Callable, Iterator

    from nu.domains.shape import Shape
    from nu.lang import Nu
    from nu.lang.runtime import Context, Runtime


__all__ = ["Frame"]


class Frame(_LifecycleBracket):
    """Runs ``body`` with a fresh dict as the mem store for ``shape``.

    On entry the frame binds a new empty dict under ``shape`` and writes
    ``initial`` into its slots. The body reads and writes the Shape's mem
    refs against that dict. On exit the prior binding comes back and the dict
    is dropped, on a clean exit, an error or a cancel alike.

    Args:
        shape: the Shape whose mem refs the frame backs.
        body: runs with the frame bound.
        **initial: a starting value per slot, a plain value or a Nu term.
            Each is evaluated once on entry, in keyword order, and written
            through the slot's ``set``.

    Notes:
        - Every run gets its own dict. Parallel arms, concurrent requests
          and nested calls each entering the frame never see each other's
          values; arms started inside one frame share its dict.
        - A frame over a Shape shadows an outer frame over the same Shape
          for its body. Frames over different Shapes coexist.
        - State that outlives one call, such as a throttle's last run inside
          a loop, needs the frame around the loop, not inside it.
        - Reading a Shape's mem ref with no frame or binding for it in scope
          raises ``LookupError`` naming the Shape.
        - An ``initial`` key that is not a slot of ``shape`` raises
          ``TypeError`` at construction. An initial value that evaluates to
          EMPTY or INVALID raises on entry, as any mem write does.
        - Over a stream body the frame stays bound for the whole drain.

    Yields:
        Whatever ``body`` yields, in the body's own cardinality.

    Example:
        >>> class Tally(nu.Shape):
        ...     n = nustd.mem.IntRef.slot()
        >>> loop = nu.ForEachDo(nu.Iter([1, 2, 3]), Tally.n.set(Tally.n + nu.Attr("item")))
        >>> _ = nu.run(nustd.mem.Frame(Tally, loop >> nu.print(Tally.n), n=0))
        6
    """

    def __init__(self, shape: type[Shape], body: Nu, **initial: object) -> None:
        unknown = [key for key in initial if key not in shape._slots]
        if unknown:
            msg = f"Frame over {shape.__name__}: {unknown} are not slots of {shape.__name__}"
            raise TypeError(msg)
        super().__init__(body, *(getattr(shape, key).set(value) for key, value in initial.items()))
        self._payload["shape"] = shape

    @contextmanager
    def _open(self, ctx: Context) -> Iterator[None]:
        with ctx.fabrics.bind(dict, {}, self._payload["shape"]):
            yield

    def _compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        body, initial = children[0], children[1:]

        def framed(rt: Runtime) -> object:
            for write in initial:
                write(rt)
            return body(rt)

        return super()._compile(nid, (framed,))

    def _acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        body, initial = children[0], children[1:]

        async def framed(rt: Runtime) -> object:
            for write in initial:
                await write(rt)
            return await body(rt)

        return super()._acompile(nid, (framed,))
