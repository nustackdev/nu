"""NuRuntime - sentinel-aware Runtime for Nu the language.

Extends the engine's generic ``Runtime`` with the Nu propagation rule: if any
operand is EMPTY or INVALID, the result is INVALID. The variants below mirror
the generic toolkit one-for-one.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from nu2.engine.execute.driver import Runtime


if TYPE_CHECKING:
    from collections.abc import Iterable

    from nu2.engine.attribution.program import Path

__all__ = ["NuRuntime"]


class NuRuntime(Runtime):
    """Sentinel-aware Runtime. Adds the ``*_or_short`` toolkit on top of the engine.

    Atoms in Nu's standard core (``nu2.core``) receive a ``NuRuntime`` from
    ``lang.entry``; they use ``rt.eval_kids_or_short`` etc. to participate in
    the Query propagation rule. Sequential and parallel variants are provided.
    """

    # --- sentinel-propagating evaluation -----------------------------------

    def eval_or_short(self, paths: Iterable[Path]) -> list | object:
        """Evaluate every path, short-circuiting on a sentinel.

        Implements the Query propagation rule: if any operand is EMPTY or
        INVALID, the result is INVALID. Otherwise returns the values list.

        Use in a ScalarQuery's ``eval``::

            values = rt.eval_or_short(rt.children(path))
            return values if is_sentinel(values) else sum(values)
        """
        from nu2.lang.sentinels import INVALID, is_sentinel

        values: list = []
        for p in paths:
            v = self.eval(p)
            if is_sentinel(v):
                return INVALID
            values.append(v)
        return values

    async def aeval_or_short(self, paths: Iterable[Path]) -> list | object:
        """Async variant of ``eval_or_short``."""
        from nu2.lang.sentinels import INVALID, is_sentinel

        values: list = []
        for p in paths:
            v = await self.aeval(p)
            if is_sentinel(v):
                return INVALID
            values.append(v)
        return values

    def eval_kids_or_short(self, path: Path) -> list | object:
        """Sugar: ``eval_or_short(rt.children(path))``."""
        return self.eval_or_short(self.children(path))

    async def aeval_kids_or_short(self, path: Path) -> list | object:
        """Sugar: ``aeval_or_short(rt.children(path))``."""
        return await self.aeval_or_short(self.children(path))

    # --- sentinel-propagating parallel -------------------------------------

    def eval_parallel_or_short(self, paths: Iterable[Path]) -> list | object:
        """Parallel ``eval`` with sentinel propagation; returns INVALID on any.

        Branches still all run (they have already been dispatched to the pool);
        the propagation rule applies to the aggregated result.
        """
        from nu2.lang.sentinels import INVALID, is_sentinel

        values = self.eval_parallel(paths)
        return INVALID if any(is_sentinel(v) for v in values) else values

    async def aeval_parallel_or_short(self, paths: Iterable[Path]) -> list | object:
        """Async parallel with sentinel propagation."""
        from nu2.lang.sentinels import INVALID, is_sentinel

        values = await self.aeval_parallel(paths)
        return INVALID if any(is_sentinel(v) for v in values) else values
