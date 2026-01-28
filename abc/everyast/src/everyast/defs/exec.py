"""Exec -- base for all topology nodes."""

from __future__ import annotations

from everyast.ast import Node


__all__ = [
    "Exec",
]


class Exec(Node["Exec"]):
    """Base for all topology nodes: Term, Flow, Span.

    Extends ``Node["Exec"]`` so all inherited methods (``append``,
    ``with_children``, ``children``, ``__getitem__``, etc.) return
    ``Exec``-typed values instead of bare ``Node``.

    Downstream packages add semantic behavior (needs, provides, etc.).
    """

    __slots__ = ()
