"""Executable -- base for all topology nodes."""

from __future__ import annotations

from .node import Node


__all__ = [
    "Executable",
]


class Executable[ChildT: Executable](Node[ChildT]):
    """Base for all topology nodes: Term, Flow, Span.

    Extends ``Node["Executable"]`` so all inherited methods (``append``,
    ``with_children``, ``children``, ``__getitem__``, etc.) return
    ``Executable``-typed values instead of bare ``Node``.

    Downstream packages add semantic behavior (needs, provides, etc.).
    """

    pass
