"""``let``: a frame for one disposable value, reached through the ref it hands you.

Some values are wanted by one body and by nothing after it: a counter for one
loop, an accumulator for one reduction. Declaring a Shape for each is more
ceremony than the value is worth. ``let`` declares it for you: one anonymous
Shape with one slot, a ``Frame`` over it, and the slot's ref handed to the
function that builds the body.

The anonymous Shape belongs to the function's code, the lambda as written in
the source. Each lambda gets its own Shape, so lets nested in each other never
share one, and building the same source twice gives the same Shapes and equal
trees. Nothing is counted or kept while a tree is being built.

The function runs once, at construction, and only builds the tree. Like any
Nu constructor, what it receives is a tree, not a value: it may shape the
body but never branches on or computes with what the ref will hold.
"""

from __future__ import annotations

import types
from functools import cache
from typing import TYPE_CHECKING

from nu.domains.shape import Shape

from ..refs import ObjectRef
from .frame import Frame


if TYPE_CHECKING:
    from collections.abc import Callable

    from nu.lang import Nu


__all__ = ["let"]


@cache
def _held(code: types.CodeType) -> type[Shape]:
    """The one-slot Shape the lets built by ``code`` bind, the same class every time."""

    def body(ns: dict[str, object]) -> None:
        ns["held"] = ObjectRef.slot()
        ns["__module__"] = __name__

    return types.new_class(f"Let_{code.co_firstlineno}", (Shape,), exec_body=body)


def let(value: object, fn: Callable[[ObjectRef], Nu]) -> Frame:
    """Runs the body ``fn`` builds with ``value`` held in a fresh mem slot.

    ``fn`` is called once, at construction, with the mem ref to the slot, and
    returns the body. The body reads the value through that ref and may
    ``.set()`` it; the slot and whatever it holds are gone when the body ends.

    ``fn`` builds a tree and nothing else. The ref it gets, like everything
    passed into a Nu constructor, is a tree even when ``value`` is a literal:
    build-time Python may shape the body but never branches on or computes
    with the value going into it. Decisions over the value are nodes of the
    body (``nu.If``, ``nu.Add``) and happen when it runs.

    The common slip is to reach for Python over the value. A Python ``if``,
    ``and``/``or`` or ``len()`` runs once, while the tree is built: on a ref
    it raises, and on a literal it quietly bakes one answer into every run.
    Build the expression instead::

        nu.let(price, lambda p: nu.print(nu.If(p > 100, "high", "low")))

    and never ``nu.print("high" if price > 100 else "low")``.

    Args:
        value: the slot's starting value, a plain value or a Nu term. Evaluated
            once on entry, like a ``Frame`` initial.
        fn: builds the body from the slot's ref. A function, so its code can
            name the slot's Shape.

    Notes:
        - The ref is always an ``ObjectRef``; nothing is inferred from
          ``value``. Wrap it in a form for a typed surface
          (``nu.Int(ref) + 1``).
        - Every run gets its own slot, so parallel arms and concurrent runs
          never see each other's value. A ``let`` built inside another's
          ``fn`` gets its own slot too, and the outer ref stays readable.
        - One ``fn`` always binds the same Shape. Calling ``let`` with it
          again inside its own body shadows the outer slot.
        - Over a stream body the slot stays bound for the whole drain.

    Yields:
        Whatever the body yields, in the body's own cardinality.

    Example:
        >>> count = lambda n: nu.ForEachDo(nu.Iter("abc"), n.set(n + 1)) >> nu.print(n)
        >>> _ = nu.run(nu.let(0, count))
        3
    """
    code = getattr(fn, "__code__", None)
    if not isinstance(code, types.CodeType):
        msg = f"let needs a function to build its body, got {type(fn).__name__}"
        raise TypeError(msg)
    shape = _held(code)
    return Frame(shape, fn(shape.held), held=value)  # type: ignore[attr-defined]
