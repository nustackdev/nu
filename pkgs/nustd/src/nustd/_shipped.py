"""Teleport args: values the sender evaluates and ships to a worker with the body.

Every Teleport (``nustd.mp`` ``Teleport`` / ``Dispatch``, ``nustd.cluster``
``Teleport``) takes its body the same way, as a lambda with its values by
parameter name, the rule ``let`` follows::

    Teleport(pool, lambda root, n: body(root, n), root=some_term, n=other_term)

At build the lambda is turned into a body over a generated Shape
(:meth:`nu.lang.binding.Binding.of_named`), and the value terms become children of the
Teleport, so the sender evaluates them. At run the body crosses as one term,
:class:`Shipped`, holding the body, the binding and the values: on the
remote side it pushes a frame with the values on the worker's own Context and
runs the body there. No sender context crosses.

The generated Shape is not importable by name, so cloudpickle pickles it by
value inside the same message as the body that reads it, and both ends agree
on one class within a message. A plain tree body takes no values and crosses
as itself.
"""

from __future__ import annotations

from contextlib import contextmanager
from typing import TYPE_CHECKING

from nu.lang import Bracket


if TYPE_CHECKING:
    from collections.abc import Iterator, Sequence

    from nu.lang.binding import Binding
    from nu.lang.runtime import Context


__all__ = ["Shipped", "shipped"]


class Shipped(Bracket):
    """A body with the values its sender evaluated, run in a frame of their own on arrival.

    Built by the sender per call, never by hand. The values are fields, not
    children: they are already evaluated and cross as data.
    """

    def __init__(self, binding: Binding, values: Sequence[object], body: object) -> None:
        self._binding = binding
        self._values = tuple(values)
        super().__init__(body)

    @contextmanager
    def _open(self, ctx: Context) -> Iterator[Context]:
        yield self._binding.push(ctx, *self._values)


def shipped(binding: Binding, values: Sequence[object], body: object) -> object:
    """The term that crosses: ``body`` itself when it reads nothing, else a :class:`Shipped`."""
    if binding.shape is None:
        return body
    return Shipped(binding, values, body)
