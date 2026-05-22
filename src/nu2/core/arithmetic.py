"""Arithmetic atoms: literals and the numeric ScalarQueries.

Concrete ScalarQuery kinds on ``nu2.lang``. A Literal carries a constant in
its payload; Add and Mul are commutative and associative, Sub, Div and Neg
are neither. None touch the Context on their own - effects come from Ref
children.

Each atom implements ``eval`` and ``aeval``. Operand evaluation goes through
the Runtime toolkit (``eval_kids_or_short`` / ``aeval_kids_or_short``) so an
EMPTY or INVALID operand collapses the result to INVALID without folding.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from nu2.engine.structure import Attribute
from nu2.lang import ScalarQuery
from nu2.lang.sentinels import EMPTY, INVALID


if TYPE_CHECKING:
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

    def eval(self, rt: Runtime, nid: int) -> object:  # noqa: D102
        return self.payload["value"]

    async def aeval(self, rt: Runtime, nid: int) -> object:  # noqa: D102
        return self.payload["value"]


class Add(ScalarQuery):
    """The sum of its scalar children."""

    commutative = Attribute.declared(True)
    associative = Attribute.declared(True)

    def eval(self, rt: Runtime, nid: int) -> object:  # noqa: D102
        s = 0
        for cnid in rt.program.kids[nid]:
            v = rt.eval(cnid)
            if v is EMPTY or v is INVALID:
                return INVALID
            s += v
        return s

    async def aeval(self, rt: Runtime, nid: int) -> object:  # noqa: D102
        s = 0
        for cnid in rt.program.kids[nid]:
            v = await rt.aeval(cnid)
            if v is EMPTY or v is INVALID:
                return INVALID
            s += v
        return s


class Mul(ScalarQuery):
    """The product of its scalar children."""

    commutative = Attribute.declared(True)
    associative = Attribute.declared(True)

    def eval(self, rt: Runtime, nid: int) -> object:  # noqa: D102
        out: object = 1
        for cnid in rt.program.kids[nid]:
            v = rt.eval(cnid)
            if v is EMPTY or v is INVALID:
                return INVALID
            out = out * v
        return out

    async def aeval(self, rt: Runtime, nid: int) -> object:  # noqa: D102
        out: object = 1
        for cnid in rt.program.kids[nid]:
            v = await rt.aeval(cnid)
            if v is EMPTY or v is INVALID:
                return INVALID
            out = out * v
        return out


class Sub(ScalarQuery):
    """The first child minus the second."""

    def eval(self, rt: Runtime, nid: int) -> object:  # noqa: D102
        kids = rt.program.kids[nid]
        a = rt.eval(kids[0])
        if a is EMPTY or a is INVALID:
            return INVALID
        b = rt.eval(kids[1])
        if b is EMPTY or b is INVALID:
            return INVALID
        return a - b

    async def aeval(self, rt: Runtime, nid: int) -> object:  # noqa: D102
        kids = rt.program.kids[nid]
        a = await rt.aeval(kids[0])
        if a is EMPTY or a is INVALID:
            return INVALID
        b = await rt.aeval(kids[1])
        if b is EMPTY or b is INVALID:
            return INVALID
        return a - b


class Div(ScalarQuery):
    """The first child divided by the second."""

    def eval(self, rt: Runtime, nid: int) -> object:  # noqa: D102
        kids = rt.program.kids[nid]
        a = rt.eval(kids[0])
        if a is EMPTY or a is INVALID:
            return INVALID
        b = rt.eval(kids[1])
        if b is EMPTY or b is INVALID:
            return INVALID
        return a / b

    async def aeval(self, rt: Runtime, nid: int) -> object:  # noqa: D102
        kids = rt.program.kids[nid]
        a = await rt.aeval(kids[0])
        if a is EMPTY or a is INVALID:
            return INVALID
        b = await rt.aeval(kids[1])
        if b is EMPTY or b is INVALID:
            return INVALID
        return a / b


class Neg(ScalarQuery):
    """The arithmetic negation of its one child."""

    def eval(self, rt: Runtime, nid: int) -> object:  # noqa: D102
        (cnid,) = rt.program.kids[nid]
        v = rt.eval(cnid)
        if v is EMPTY or v is INVALID:
            return INVALID
        return -v

    async def aeval(self, rt: Runtime, nid: int) -> object:  # noqa: D102
        (cnid,) = rt.program.kids[nid]
        v = await rt.aeval(cnid)
        if v is EMPTY or v is INVALID:
            return INVALID
        return -v
