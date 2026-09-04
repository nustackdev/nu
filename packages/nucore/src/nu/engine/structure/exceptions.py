"""Exceptions raised by the structure module."""

from __future__ import annotations


__all__ = ["CycleError", "NotFinalizedError"]


class CycleError(Exception):
    """The cross-attribute dependency graph contains a cycle.

    Raised by ``Schema.finalize`` when the read-graph (each computed
    attribute's ``reads``) cannot be topologically ordered.
    """


class NotFinalizedError(RuntimeError):
    """A finalized schema is required.

    Raised when an operation that depends on the topological order is
    invoked before :meth:`Schema.finalize`.
    """
