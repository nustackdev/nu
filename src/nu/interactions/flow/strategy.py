"""Parallel ops -- ParAny.

``Race`` and ``ParAll`` are deleted: the new core ships
``nu.terms.flow.Race`` and ``nu.terms.flow.Parallel`` (was ``ParAll``).
Top-level ``nu.Race`` and ``nu.Parallel`` resolve there.

``ParAny`` stays as a distinct semantic over concurrent children:
succeed if any child succeeds.
"""

from __future__ import annotations

import asyncio
from typing import TYPE_CHECKING, Any, ClassVar

from nu.terms.flow import Strategy
from nu.terms.types import Mode


if TYPE_CHECKING:
    from nu.terms import Nu


__all__ = [
    "ParAny",
]


class ParAny(Strategy):
    """Run children concurrently; succeed if any one succeeds.

    Children: ``[*children]`` -- all body slots (Strategy semantics).
    """

    support: ClassVar[frozenset[Mode]] = frozenset({Mode.ASYNC})

    def __init__(self, *children: Nu) -> None:
        super().__init__(*children)

    async def _arun_children(self, ctx: Any) -> None:  # noqa: ANN401
        from nu import runtime

        if not self._children:
            return
        tasks = {asyncio.create_task(runtime.aexecute(child, ctx)) for child in self._children}
        last_error: BaseException | None = None
        try:
            while tasks:
                done, tasks = await asyncio.wait(
                    tasks,
                    return_when=asyncio.FIRST_COMPLETED,
                )
                for task in done:
                    exc = task.exception()
                    if exc is None:
                        for t in tasks:
                            t.cancel()
                        if tasks:
                            await asyncio.gather(*tasks, return_exceptions=True)
                        return
                    last_error = exc
            if last_error is not None:
                raise last_error
        except BaseException:
            for task in tasks:
                task.cancel()
            if tasks:
                await asyncio.gather(*tasks, return_exceptions=True)
            raise
