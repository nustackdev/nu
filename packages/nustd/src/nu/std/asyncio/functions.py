"""Module-level functions for ``nu.std.asyncio`` - the function namespace.

``asyncio`` has no central class, and its orchestration surface (``gather``,
``wait``, ``create_task``, ``run``) maps onto Nu Flows, not onto atoms. So the
only free function here is the leaf primitive Flows can't provide: ``sleep``.

``sleep`` -> ``None_`` (an effect-only ScalarQuery; it yields ``None``, it just
suspends). It is async-only - see ``interactions``. The sync, blocking sibling is
``nu.std.time.sleep``.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from nu.forms import None_


if TYPE_CHECKING:
    from nu.lang import FloatArg


__all__ = ["sleep"]


def sleep(delay: FloatArg) -> None_:
    """Suspend for ``delay`` seconds without blocking the loop: mirrors ``asyncio.sleep()``. Async-only."""
    from .interactions import AsyncioSleep

    return None_(AsyncioSleep(delay))
