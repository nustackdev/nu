"""Logic atoms: comparison and boolean ScalarQueries.

Concrete ScalarQuery kinds that yield a boolean. And and Or are commutative,
associative and idempotent; Eq is commutative; Lt and Not are neither. Eager
evaluation - And and Or fold every operand instead of short-circuiting, so
sentinel propagation has the chance to fire on any branch.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from nu2.engine.structure import Attribute
from nu2.lang import ScalarQuery
from nu2.lang.sentinels import is_sentinel


if TYPE_CHECKING:
    from nu2.engine.attribution.program import Path
    from nu2.lang.runtime import NuRuntime as Runtime

__all__ = ["And", "Eq", "Lt", "Not", "Or"]


class Eq(ScalarQuery):
    """Whether its two children are equal."""

    commutative = Attribute.declared(True)

    def eval(self, rt: Runtime, path: Path) -> object:  # noqa: D102
        values = rt.eval_kids_or_short(path)
        if is_sentinel(values):
            return values
        a, b = values
        return a == b

    async def aeval(self, rt: Runtime, path: Path) -> object:  # noqa: D102
        values = await rt.aeval_kids_or_short(path)
        if is_sentinel(values):
            return values
        a, b = values
        return a == b


class Lt(ScalarQuery):
    """Whether the first child is less than the second."""

    def eval(self, rt: Runtime, path: Path) -> object:  # noqa: D102
        values = rt.eval_kids_or_short(path)
        if is_sentinel(values):
            return values
        a, b = values
        return a < b

    async def aeval(self, rt: Runtime, path: Path) -> object:  # noqa: D102
        values = await rt.aeval_kids_or_short(path)
        if is_sentinel(values):
            return values
        a, b = values
        return a < b


class And(ScalarQuery):
    """The conjunction of its boolean children."""

    commutative = Attribute.declared(True)
    associative = Attribute.declared(True)
    idempotent = Attribute.declared(True)

    def eval(self, rt: Runtime, path: Path) -> object:  # noqa: D102
        values = rt.eval_kids_or_short(path)
        return values if is_sentinel(values) else all(values)

    async def aeval(self, rt: Runtime, path: Path) -> object:  # noqa: D102
        values = await rt.aeval_kids_or_short(path)
        return values if is_sentinel(values) else all(values)


class Or(ScalarQuery):
    """The disjunction of its boolean children."""

    commutative = Attribute.declared(True)
    associative = Attribute.declared(True)
    idempotent = Attribute.declared(True)

    def eval(self, rt: Runtime, path: Path) -> object:  # noqa: D102
        values = rt.eval_kids_or_short(path)
        return values if is_sentinel(values) else any(values)

    async def aeval(self, rt: Runtime, path: Path) -> object:  # noqa: D102
        values = await rt.aeval_kids_or_short(path)
        return values if is_sentinel(values) else any(values)


class Not(ScalarQuery):
    """The negation of its one boolean child."""

    def eval(self, rt: Runtime, path: Path) -> object:  # noqa: D102
        values = rt.eval_kids_or_short(path)
        if is_sentinel(values):
            return values
        (a,) = values
        return not a

    async def aeval(self, rt: Runtime, path: Path) -> object:  # noqa: D102
        values = await rt.aeval_kids_or_short(path)
        if is_sentinel(values):
            return values
        (a,) = values
        return not a
