"""Range iteration Flow Command -- ForRange.

``ForEach`` is deleted; the new core ships ``nu.terms.flow.ForEachDo``
which is the canonical Control variant. Top-level ``nu.ForEachDo``
resolves there.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, ClassVar

from nu.terms.flow import Control
from nu.terms.types import Mode


if TYPE_CHECKING:
    from nu.terms import IntArg, Nu, StrArg


__all__ = [
    "ForRange",
]


_BOTH = frozenset({Mode.SYNC, Mode.ASYNC})


class ForRange(Control):
    """Counted loop over ``range(start, stop, step)``.

    Children: ``[start, stop, step, body]`` or
    ``[start, stop, step, body, index_key]``. Body lives at slot 3.

    Sets ``ctx.attrs[index_key]`` to the current loop value each
    iteration when an index key is provided.
    """

    body_slots: ClassVar[tuple[int, ...]] = (3,)
    support: ClassVar[frozenset[Mode]] = _BOTH

    def __init__(
        self,
        start: IntArg,
        stop: IntArg,
        body: Nu,
        *,
        step: IntArg = 1,
        index: StrArg | None = None,
    ) -> None:
        self._has_index = index is not None
        children: list = [start, stop, step, body]
        if index is not None:
            children.append(index)
        super().__init__(*children)

    def run(self, ctx: Any) -> None:  # noqa: ANN401
        from nu import runtime

        start = runtime.first(self._children[0], ctx)
        stop = runtime.first(self._children[1], ctx)
        step = runtime.first(self._children[2], ctx)
        body = self._children[3]

        index_key: str | None = None
        if self._has_index:
            index_key = runtime.first(self._children[4], ctx)

        for i in range(start, stop, step):
            if index_key is not None:
                ctx.attrs[index_key] = i
            runtime.execute(body, ctx)

    async def arun(self, ctx: Any) -> None:  # noqa: ANN401
        from nu import runtime

        start = await runtime.afirst(self._children[0], ctx)
        stop = await runtime.afirst(self._children[1], ctx)
        step = await runtime.afirst(self._children[2], ctx)
        body = self._children[3]

        index_key: str | None = None
        if self._has_index:
            index_key = await runtime.afirst(self._children[4], ctx)

        for i in range(start, stop, step):
            if index_key is not None:
                ctx.attrs[index_key] = i
            await runtime.aexecute(body, ctx)
