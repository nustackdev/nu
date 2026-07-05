"""Conditional atoms: value-yielding branch selection.

Maps Python's conditional expression (``x if cond else y``) and mapping-based
dispatch onto Nu ScalarQueries. Pure compute; no Context effect of their own.
Siblings to the mutating ``IfDo`` / ``SwitchDo`` in ``nu.flows.control`` - same
name family, different sort: the ``Do`` variants run one of N bodies for
effect and yield nothing; the ``Query`` variants yield one of N values and
mutate nothing.

Sorts: all ScalarQuery (Q).

Short-circuit: only the taken branch is evaluated - matches Python's
conditional expression, and lets ``IfQuery(cond, safe, unsafe)`` guard the
``unsafe`` branch from firing when ``cond`` is truthy.

Sentinels: an ``EMPTY`` or ``INVALID`` selector/condition collapses to
``INVALID`` (per ``nu.lang.sentinels``); an ``EMPTY`` / ``INVALID`` result on
the taken branch propagates through as ``INVALID``.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from nu.lang import ScalarQuery
from nu.lang.sentinels import EMPTY, INVALID


if TYPE_CHECKING:
    from collections.abc import Callable, Mapping

    from nu.engine import Term
    from nu.lang.runtime import Runtime

__all__ = ["IfQuery", "SwitchQuery"]


class IfQuery(ScalarQuery):
    """``IfQuery(cond, then, else_)`` - yield ``then`` if ``cond`` truthy, else ``else_``.

    Children: ``[cond, then, else_]``. Short-circuits: only the taken branch
    is evaluated.
    """

    def _compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:  # noqa: D102
        cond, then_, else_ = children

        def thunk(rt: Runtime) -> object:
            c = cond(rt)
            if c is EMPTY or c is INVALID:
                return INVALID
            v = then_(rt) if c else else_(rt)
            if v is EMPTY or v is INVALID:
                return INVALID
            return v

        return thunk

    def _acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:  # noqa: D102
        cond, then_, else_ = children

        async def athunk(rt: Runtime) -> object:
            c = await cond(rt)
            if c is EMPTY or c is INVALID:
                return INVALID
            v = await (then_(rt) if c else else_(rt))
            if v is EMPTY or v is INVALID:
                return INVALID
            return v

        return athunk


class SwitchQuery(ScalarQuery):
    """``SwitchQuery(selector, cases, default=None)`` - yield the value for the matching key.

    Children: ``[selector, *case_values, default?]``. The match keys are
    intrinsic constants kept in ``payload`` (so they survive
    ``with_children``), paired by position with the case values. The first
    key equal to the selector value yields its case value; failing any
    match, the optional default yields; failing that, ``INVALID``.

    Short-circuits: only the matching case value is evaluated. Sibling to
    the mutating :class:`nu.flows.control.SwitchDo`.
    """

    def __init__(
        self,
        selector: object,
        cases: Mapping[object, Term],
        default: object = None,
    ) -> None:
        values = list(cases.values())
        if default is not None:
            values.append(default)
        super().__init__(selector, *values)
        self._payload["keys"] = tuple(cases.keys())
        self._payload["has_default"] = default is not None

    def _compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:  # noqa: D102
        selector = children[0]
        values = children[1:]
        keys = self._payload["keys"]
        has_default = self._payload["has_default"]

        def thunk(rt: Runtime) -> object:
            s = selector(rt)
            if s is EMPTY or s is INVALID:
                return INVALID
            for i, key in enumerate(keys):
                if key == s:
                    v = values[i](rt)
                    if v is EMPTY or v is INVALID:
                        return INVALID
                    return v
            if has_default:
                v = values[-1](rt)
                if v is EMPTY or v is INVALID:
                    return INVALID
                return v
            return INVALID

        return thunk

    def _acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:  # noqa: D102
        selector = children[0]
        values = children[1:]
        keys = self._payload["keys"]
        has_default = self._payload["has_default"]

        async def athunk(rt: Runtime) -> object:
            s = await selector(rt)
            if s is EMPTY or s is INVALID:
                return INVALID
            for i, key in enumerate(keys):
                if key == s:
                    v = await values[i](rt)
                    if v is EMPTY or v is INVALID:
                        return INVALID
                    return v
            if has_default:
                v = await values[-1](rt)
                if v is EMPTY or v is INVALID:
                    return INVALID
                return v
            return INVALID

        return athunk
