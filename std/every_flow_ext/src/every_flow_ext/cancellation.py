"""Cancellation support -- flows and tree transforms."""

from __future__ import annotations

from typing import TYPE_CHECKING

from every_flow import Seq, Var
from every_flow.loops import ForRange, While
from everyabc import Flow, map_nodes


if TYPE_CHECKING:
    from everyabc import Context, Exec


__all__ = [
    "CancelledError",
    "CheckCancellation",
    "add_cancellation_checks",
]


class CancelledError(Exception):
    """Raised when a flow detects cancellation."""


class CheckCancellation(Flow):
    """Leaf flow that checks a cancellation Var and raises if True.

    Example::

        cancelled = Var(False)
        check = CheckCancellation(cancelled)
        check.execute(ctx)  # passes

        cancelled.set(True)
        check.execute(ctx)  # raises CancelledError
    """

    __slots__ = ("_cancelled",)

    def __init__(self, cancelled: Var[bool]) -> None:
        """Initialize with a Var[bool] to check."""
        super().__init__()
        self._cancelled = cancelled

    def execute(self, ctx: Context) -> None:
        """Raise CancelledError if the cancelled var is True."""
        if self._cancelled.get():
            raise CancelledError


def add_cancellation_checks(root: Exec, cancelled: Var[bool]) -> Exec:
    """Insert cancellation checks into loop bodies.

    Tree transform: finds While and ForRange nodes, wraps their
    body child in Seq(CheckCancellation(cancelled), original_body).

    Args:
        root: Root of the topology tree.
        cancelled: Var[bool] checked at each loop iteration.

    Returns:
        New tree with cancellation checks inserted.
    """
    check = CheckCancellation(cancelled)

    def _inject(node: Exec) -> Exec:
        if isinstance(node, While):
            body = node.children[1]
            new_body = Seq(check, body)
            return While(node.children[0], new_body)
        if isinstance(node, ForRange):
            body = node.children[3]
            new_body = Seq(check, body)
            return ForRange(
                node.children[0],
                node.children[1],
                new_body,
                step=node.children[2],
                index=node._index,
            )
        return node

    return map_nodes(root, _inject, order="bottom_up")
