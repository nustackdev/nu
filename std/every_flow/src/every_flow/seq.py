"""Seq -- sequential execution flow."""

from __future__ import annotations

from typing import TYPE_CHECKING

from everyabc import Flow


if TYPE_CHECKING:
    from everyabc import Executable


__all__ = [
    "Seq",
]


class Seq(Flow):
    """Execute children sequentially.

    Inherits Flow's default execute() which already runs
    children in order. This class exists for explicit naming.

    Example::

        Seq(step_a, step_b, step_c)
    """

    def __init__(self, *children: Executable) -> None:
        """Initialize with children to execute in order."""
        super().__init__(*children)
