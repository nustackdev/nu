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
from nu2.lang.sentinels import EMPTY, INVALID


if TYPE_CHECKING:
    from nu2.lang.runtime import NuRuntime as Runtime

__all__ = ["And", "Eq", "Lt", "Not", "Or"]


class Eq(ScalarQuery):
    """Whether its two children are equal."""

    commutative = Attribute.declared(True)

    def eval(self, rt: Runtime, nid: int) -> object:  # noqa: D102
        kids = rt.program.kids[nid]
        a = rt.eval(kids[0])
        if a is EMPTY or a is INVALID:
            return INVALID
        b = rt.eval(kids[1])
        if b is EMPTY or b is INVALID:
            return INVALID
        return a == b

    async def aeval(self, rt: Runtime, nid: int) -> object:  # noqa: D102
        kids = rt.program.kids[nid]
        a = await rt.aeval(kids[0])
        if a is EMPTY or a is INVALID:
            return INVALID
        b = await rt.aeval(kids[1])
        if b is EMPTY or b is INVALID:
            return INVALID
        return a == b


class Lt(ScalarQuery):
    """Whether the first child is less than the second."""

    def eval(self, rt: Runtime, nid: int) -> object:  # noqa: D102
        kids = rt.program.kids[nid]
        a = rt.eval(kids[0])
        if a is EMPTY or a is INVALID:
            return INVALID
        b = rt.eval(kids[1])
        if b is EMPTY or b is INVALID:
            return INVALID
        return a < b

    async def aeval(self, rt: Runtime, nid: int) -> object:  # noqa: D102
        kids = rt.program.kids[nid]
        a = await rt.aeval(kids[0])
        if a is EMPTY or a is INVALID:
            return INVALID
        b = await rt.aeval(kids[1])
        if b is EMPTY or b is INVALID:
            return INVALID
        return a < b


class And(ScalarQuery):
    """The conjunction of its boolean children."""

    commutative = Attribute.declared(True)
    associative = Attribute.declared(True)
    idempotent = Attribute.declared(True)

    def eval(self, rt: Runtime, nid: int) -> object:  # noqa: D102
        out = True
        for cnid in rt.program.kids[nid]:
            v = rt.eval(cnid)
            if v is EMPTY or v is INVALID:
                return INVALID
            out = out and bool(v)
        return out

    async def aeval(self, rt: Runtime, nid: int) -> object:  # noqa: D102
        out = True
        for cnid in rt.program.kids[nid]:
            v = await rt.aeval(cnid)
            if v is EMPTY or v is INVALID:
                return INVALID
            out = out and bool(v)
        return out


class Or(ScalarQuery):
    """The disjunction of its boolean children."""

    commutative = Attribute.declared(True)
    associative = Attribute.declared(True)
    idempotent = Attribute.declared(True)

    def eval(self, rt: Runtime, nid: int) -> object:  # noqa: D102
        out = False
        for cnid in rt.program.kids[nid]:
            v = rt.eval(cnid)
            if v is EMPTY or v is INVALID:
                return INVALID
            out = out or bool(v)
        return out

    async def aeval(self, rt: Runtime, nid: int) -> object:  # noqa: D102
        out = False
        for cnid in rt.program.kids[nid]:
            v = await rt.aeval(cnid)
            if v is EMPTY or v is INVALID:
                return INVALID
            out = out or bool(v)
        return out


class Not(ScalarQuery):
    """The negation of its one boolean child."""

    def eval(self, rt: Runtime, nid: int) -> object:  # noqa: D102
        (cnid,) = rt.program.kids[nid]
        v = rt.eval(cnid)
        if v is EMPTY or v is INVALID:
            return INVALID
        return not v

    async def aeval(self, rt: Runtime, nid: int) -> object:  # noqa: D102
        (cnid,) = rt.program.kids[nid]
        v = await rt.aeval(cnid)
        if v is EMPTY or v is INVALID:
            return INVALID
        return not v
