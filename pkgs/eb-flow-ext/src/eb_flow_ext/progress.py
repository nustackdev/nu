"""Progress tracking -- flows and tree transforms."""

from __future__ import annotations

from typing import TYPE_CHECKING

from eb_flow import Var
from everybase import Flow, map_nodes


if TYPE_CHECKING:
    from everybase import Context, Executable


__all__ = [
    "Progress",
    "add_progress",
]


class Progress(Flow):
    """Wraps children with lifecycle tracking via Vars.

    Tracks started/finished/error state through Var references.
    On execute: sets started=True, runs children, sets finished=True.
    On error: writes error message to error Var, re-raises.

    Example::

        started = Var(False)
        finished = Var(False)
        error = Var("")
        p = Progress(child, started=started, finished=finished, error=error)
        await p.execute(ctx)
        assert started.get() is True
        assert finished.get() is True
    """

    def __init__(
        self,
        *children: Executable,
        started: Var[bool] | None = None,
        finished: Var[bool] | None = None,
        error: Var[str] | None = None,
    ) -> None:
        """Initialize progress tracker.

        Args:
            *children: Children to execute with lifecycle tracking.
            started: Var set to True when execution begins.
            finished: Var set to True when execution succeeds.
            error: Var set to str(exception) on failure.
        """
        super().__init__(*children)
        self._started = started or Var(False)
        self._finished = finished or Var(False)
        self._error = error or Var("")

    async def execute(self, ctx: Context) -> None:
        """Execute children with lifecycle tracking."""
        self._started.set(True)
        self._finished.set(False)
        self._error.set("")
        try:
            for child in self.children:
                await child.execute(ctx)
            self._finished.set(True)
        except Exception as e:
            self._error.set(str(e))
            raise


def add_progress(root: Executable) -> Executable:
    """Wrap every non-Progress Flow in a Progress.

    Tree transform: walks the tree bottom-up and wraps
    each Flow node (that isn't already a Progress) in
    a new Progress node.

    Args:
        root: Root of the topology tree.

    Returns:
        New tree with Progress wrappers.
    """

    def _wrap(node: Executable) -> Executable:
        if isinstance(node, Flow) and not isinstance(node, Progress):
            return Progress(node)
        return node

    return map_nodes(root, _wrap, order="bottom_up")
