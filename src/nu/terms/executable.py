"""Executable — base for all topology nodes."""

from __future__ import annotations

from abc import abstractmethod
from typing import Any

from .node import Node


__all__ = [
    "Executable",
]


class Executable[ChildT: Executable](Node[ChildT]):
    """Base for all topology nodes: Term, Flow, Span.

    Extends ``Node["Executable"]`` so all inherited methods (``append``,
    ``with_children``, ``children``, ``__getitem__``, etc.) return
    ``Executable``-typed values instead of bare ``Node``.

    All topology nodes must implement ``execute(ctx)``.
    """

    @abstractmethod
    async def execute(self, ctx: Any) -> Any:  # noqa: ANN401
        """Execute this node within a context."""
        ...
