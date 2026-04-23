"""Time-backed Commands. SYNC-mode wrappers over the ``time`` module."""

from __future__ import annotations

import time
from typing import TYPE_CHECKING, ClassVar

from nu.terms import Mode, UnaryAtomic


if TYPE_CHECKING:
    from nu.terms import FloatArg


__all__ = ["TimeSleep"]


class TimeSleep(UnaryAtomic):
    """Block the thread for ``delay`` seconds. Wraps `time.sleep`.

    Children: ``[delay]``
    """

    own_mode: ClassVar[Mode] = Mode.BOTH
    func_mode: ClassVar[Mode] = Mode.SYNC

    def __init__(self, delay: FloatArg) -> None:
        super().__init__(delay)

    def apply(self, delay: float) -> None:
        time.sleep(delay)
