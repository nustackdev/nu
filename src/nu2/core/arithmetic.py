"""Arithmetic atoms: literals and the numeric ScalarQueries.

Concrete ScalarQuery kinds on ``nu2.lang``. A Literal carries a constant in its
payload; Add and Mul are commutative and associative, Sub, Div and Neg are
neither. None touch the Context on their own - effects come from Ref children.

Each atom implements ``eval`` and ``aeval``. Operand evaluation goes through
the Runtime toolkit (``eval_or_short`` / ``aeval_or_short``) so an EMPTY or
INVALID operand collapses the result to INVALID without folding.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from nu2.engine.structure import Attribute
from nu2.lang import ScalarQuery
from nu2.lang.sentinels import is_sentinel


if TYPE_CHECKING:
    from nu2.engine.attribution.attributed_term import Path
    from nu2.lang.runtime import NuRuntime as Runtime

__all__ = ["Add", "Div", "Literal", "Mul", "Neg", "Sub"]


def _product(values: list) -> object:
    out: object = 1
    for v in values:
        out = out * v
    return out


class Literal(ScalarQuery):
    """A ScalarQuery that yields a constant value carried in its payload."""

    def __init__(self, value: object) -> None:
        super().__init__()
        self.payload = {"value": value}

    def eval(self, rt: Runtime, path: Path) -> object:  # noqa: D102
        return rt.payload(path)["value"]

    async def aeval(self, rt: Runtime, path: Path) -> object:  # noqa: D102
        return rt.payload(path)["value"]


class Add(ScalarQuery):
    """The sum of its scalar children."""

    commutative = Attribute.declared(True)
    associative = Attribute.declared(True)

    def eval(self, rt: Runtime, path: Path) -> object:  # noqa: D102
        values = rt.eval_kids_or_short(path)
        return values if is_sentinel(values) else sum(values)

    async def aeval(self, rt: Runtime, path: Path) -> object:  # noqa: D102
        values = await rt.aeval_kids_or_short(path)
        return values if is_sentinel(values) else sum(values)


class Mul(ScalarQuery):
    """The product of its scalar children."""

    commutative = Attribute.declared(True)
    associative = Attribute.declared(True)

    def eval(self, rt: Runtime, path: Path) -> object:  # noqa: D102
        values = rt.eval_kids_or_short(path)
        return values if is_sentinel(values) else _product(values)

    async def aeval(self, rt: Runtime, path: Path) -> object:  # noqa: D102
        values = await rt.aeval_kids_or_short(path)
        return values if is_sentinel(values) else _product(values)


class Sub(ScalarQuery):
    """The first child minus the second."""

    def eval(self, rt: Runtime, path: Path) -> object:  # noqa: D102
        values = rt.eval_kids_or_short(path)
        if is_sentinel(values):
            return values
        a, b = values
        return a - b

    async def aeval(self, rt: Runtime, path: Path) -> object:  # noqa: D102
        values = await rt.aeval_kids_or_short(path)
        if is_sentinel(values):
            return values
        a, b = values
        return a - b


class Div(ScalarQuery):
    """The first child divided by the second."""

    def eval(self, rt: Runtime, path: Path) -> object:  # noqa: D102
        values = rt.eval_kids_or_short(path)
        if is_sentinel(values):
            return values
        a, b = values
        return a / b

    async def aeval(self, rt: Runtime, path: Path) -> object:  # noqa: D102
        values = await rt.aeval_kids_or_short(path)
        if is_sentinel(values):
            return values
        a, b = values
        return a / b


class Neg(ScalarQuery):
    """The arithmetic negation of its one child."""

    def eval(self, rt: Runtime, path: Path) -> object:  # noqa: D102
        values = rt.eval_kids_or_short(path)
        if is_sentinel(values):
            return values
        (a,) = values
        return -a

    async def aeval(self, rt: Runtime, path: Path) -> object:  # noqa: D102
        values = await rt.aeval_kids_or_short(path)
        if is_sentinel(values):
            return values
        (a,) = values
        return -a
