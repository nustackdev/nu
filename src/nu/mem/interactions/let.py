"""``let``: binding with no logic, values handed to a body through mem.

One interaction, two forms, values always passed by slot name:

    nu.let(Tally, body, total=0)                  # Shape given: static binding
    nu.let(lambda n: body(n), n=0)                # lambda given: dynamic binding
    nu.let(lambda a, b: body(a, b), a=1, b=2)

Every run pushes a frame with a fresh dict under the Shape holding the values
and runs the body on that frame. The values are evaluated before the
push, on the Context the ``let`` runs on, so a value reading the same Shape
reads the outer frame.

With a lambda the Shape is generated from it: one slot per parameter, the
same class for the same code every time, so lets nested in each other never
share one and building the same source twice gives equal trees.

The lambda runs once, at construction, and only builds the tree. Like any Nu
constructor, what it receives is a tree, not a value: it may shape the body
but never branches on or computes with what the refs will hold.
"""

from __future__ import annotations

from contextlib import contextmanager
from typing import TYPE_CHECKING

from nu.domains.shape import Shape
from nu.lang import Bracket
from nu.lang.binding import Binding, lambda_params
from nu.lang.null import is_null
from nu.lang.sentinels import UNSET


if TYPE_CHECKING:
    from collections.abc import Iterator

    from nu.lang.runtime import Context


__all__ = ["Let", "let"]


class Let(Bracket):
    """Runs a body with values held in a fresh mem frame. Built by :func:`let`."""

    def __init__(self, target: object, body: object = UNSET, /, **values: object) -> None:
        if isinstance(target, type) and issubclass(target, Shape):
            if body is UNSET:
                msg = f"let over {target.__name__} takes the body after the Shape"
                raise TypeError(msg)
            unknown = [key for key in values if key not in target._slots]
            if unknown:
                msg = f"let over {target.__name__}: {unknown} are not slots of {target.__name__}"
                raise TypeError(msg)
            self._binding = Binding.of(target, tuple(values))
            super().__init__(body, *values.values())
            return
        if body is not UNSET:
            msg = "let(fn, **values) takes the values by name, not a body: the lambda builds it"
            raise TypeError(msg)
        lambda_params("let", target)  # a lambda, nothing else
        built, self._binding, ordered = Binding.of_named("let", target, values)
        super().__init__(built, *ordered)

    @contextmanager
    def _open(self, ctx: Context, *values: object) -> Iterator[Context]:
        shape = self._binding.shape
        for name, value in zip(self._binding.slots, values, strict=False):
            if is_null(value):
                msg = f"let: cannot store NULL in {getattr(shape, '__name__', shape)}.{name}"
                raise ValueError(msg)
        yield self._binding.push(ctx, *values)


def let(target: object, body: object = UNSET, /, **values: object) -> Let:
    """Runs a body with values held in a fresh mem frame, read through the frame's refs.

    Two forms, values always by slot name:

    - ``let(Shape, body, **values)``: static. A fresh dict is bound for
      ``Shape``, each value written to its slot, and ``body`` reads and
      writes the Shape's refs against it.
    - ``let(fn, **values)``: dynamic. A Shape is generated from ``fn``, one
      slot per parameter, and ``fn`` is called once, at construction, with
      the slots' refs; it returns the body. Every parameter takes a value.

    The body reads the values through the refs and may ``.set()`` them; the
    frame and whatever it holds are gone when the body ends.

    ``fn`` builds a tree and nothing else. The refs it gets, like everything
    passed into a Nu constructor, are trees even when a value is a literal:
    build-time Python may shape the body but never branches on or computes
    with the value going into it. Decisions over the value are nodes of the
    body (``nu.If``, ``nu.Add``) and happen when it runs::

        nu.let(lambda p: nu.print(nu.If(p > 100, "high", "low")), p=price)

    and never ``nu.print("high" if price > 100 else "low")``.

    Args:
        target: a Shape (static) or the function building the body (dynamic).
        body: the body, for the static form only.
        **values: a starting value per slot, a plain value or a Nu term. Each
            is evaluated once, before the frame is pushed, so it reads the
            Context outside the let.

    Notes:
        - A generated Shape's refs are ``ObjectRef``; nothing is inferred
          from the values. Wrap one in a form for a typed surface
          (``nu.Int(ref) + 1``).
        - Every run gets its own frame, so parallel arms and concurrent runs
          never see each other's values. Arms started inside a let share
          its frame.
        - A let over a Shape shadows an outer frame over the same Shape for
          its body; one ``fn`` always generates the same Shape, so a let
          with it inside its own body shadows the outer one.
        - State that outlives one call, such as a throttle's last run inside
          a loop, needs the let around the loop, not inside it.
        - Reading a Shape's ref with no frame for it in scope raises
          ``LookupError`` naming the Shape.
        - A value naming no slot (or no parameter), or a parameter without a
          value, raises ``TypeError`` at construction. A value that
          evaluates to NULL raises ``ValueError`` on entry.
        - Over a stream body the frame stays bound for the whole drain.

    Yields:
        Whatever the body yields, in the body's own cardinality.

    Example:
        >>> count = lambda n: nu.ForEachDo(nu.Iter("abc"), n.set(n + 1)) >> nu.print(n)
        >>> _ = nu.run(nu.let(count, n=0))
        3

        Over a declared Shape:

        >>> class Tally(nu.Shape):
        ...     count = nu.IntRef.slot()
        ...     total = nu.IntRef.slot()
        >>> step = lambda x: Tally.count.set(Tally.count + 1) >> Tally.total.set(Tally.total + x)
        >>> mean = nu.ForEachDo(nu.Iter([1, 2, 6]), step) >> nu.print(Tally.total / Tally.count)
        >>> _ = nu.run(nu.let(Tally, mean, count=0, total=0))
        3.0
    """
    return Let(target, body, **values)
