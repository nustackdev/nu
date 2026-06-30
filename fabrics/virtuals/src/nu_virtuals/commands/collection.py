"""virtuals collection commands — unsafe clear primitives.

ClearPrimitivesUnsafeCmd: Clear all primitive children — _unsafe_primitive_clear().

Requires virtuals views with UnsafePrimitiveOpsBase in MRO.
"""

from __future__ import annotations

from typing import Any, ClassVar

from nu.terms.command import ScalarCommand
from nu.terms.types import Effect, Mode


__all__ = [
    "ClearPrimitivesUnsafeCmd",
]


class ClearPrimitivesUnsafeCmd(ScalarCommand):
    """Clear all primitive children via _unsafe_primitive_clear().

    Scan + ctx.delete() each -- no validation, no descendant cleanup.
    The caller must know all children are primitives.

    The ref must implement:
        fetch(ctx) -> view with _unsafe_primitive_clear() method
    """

    own_effects: ClassVar[dict[int, Effect]] = {0: Effect.WRITE}
    support: ClassVar[frozenset[Mode]] = frozenset({Mode.SYNC, Mode.ASYNC})

    def __init__(self, ref: object) -> None:
        super().__init__(ref)
        self.ref = ref

    def run(self, ctx: Any) -> None:  # noqa: ANN401
        view = self.ref.fetch(ctx)
        view._unsafe_primitive_clear()

    async def arun(self, ctx: Any) -> None:  # noqa: ANN401
        view = await self.ref.afetch(ctx)
        view._unsafe_primitive_clear()

    def __repr__(self) -> str:
        return f"ClearPrimitivesUnsafeCmd({self.ref!r})"
