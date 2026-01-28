"""Exec -- base for all topology nodes."""

from __future__ import annotations

from .node import Node


__all__ = [
    "Exec",
]


class Exec[ChildT: Exec](Node[ChildT]):
    """Base for all topology nodes: Term, Flow, Span.

    Extends ``Node["Exec"]`` so all inherited methods (``append``,
    ``with_children``, ``children``, ``__getitem__``, etc.) return
    ``Exec``-typed values instead of bare ``Node``.

    Downstream packages add semantic behavior (needs, provides, etc.).
    """

    pass
