"""Cancellation support -- flows and tree transforms."""

from __future__ import annotations

from typing import TYPE_CHECKING

from eb_flow import Seq, Var
from eb_flow.loops import ForRange, While
from everybase import Flow, map_nodes


if TYPE_CHECKING:
    from everybase import Context, Executable


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
        await check.execute(ctx)  # passes

        cancelled.set(True)
        await check.execute(ctx)  # raises CancelledError
    """

    def __init__(self, cancelled: Var[bool]) -> None:
        """Initialize with a Var[bool] to check."""
        super().__init__()
        self._cancelled = cancelled

    async def execute(self, ctx: Context) -> None:
        """Raise CancelledError if the cancelled var is True."""
        if self._cancelled.get():
            raise CancelledError


def add_cancellation_checks(root: Executable, cancelled: Var[bool]) -> Executable:
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

    def _inject(node: Executable) -> Executable:
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
