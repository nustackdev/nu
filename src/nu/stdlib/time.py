"""Time-backed Commands. SYNC-mode wrappers over the ``time`` module."""

from __future__ import annotations

import time
from typing import TYPE_CHECKING, ClassVar

from nu.terms import Mode, UnaryCommand


if TYPE_CHECKING:
    from nu.terms import FloatArg


__all__ = ["TimeSleep"]


class TimeSleep(UnaryCommand):
    """Block the thread for ``delay`` seconds. Wraps `time.sleep`.

    Children: ``[delay]``
    """

    support: ClassVar[frozenset[Mode]] = frozenset({Mode.SYNC, Mode.ASYNC})

    def __init__(self, delay: FloatArg) -> None:
        super().__init__(delay)

    def apply(self, delay: float) -> None:
        time.sleep(delay)
