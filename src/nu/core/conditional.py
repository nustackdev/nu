"""Conditional atoms: value-yielding branch selection.

Maps Python's conditional expression (``x if cond else y``) and mapping-based
dispatch onto Nu ScalarQueries. Pure compute; no Context effect of their own.
Siblings to the mutating ``IfDo`` / ``SwitchDo`` in ``nu.core.flows.control`` - same
name family, different sort: the ``Do`` variants run one of N bodies for
effect and yield nothing; the ``Query`` variants yield one of N values and
mutate nothing.

Sorts: all ScalarQuery (Q).

Short-circuit: only the taken branch is evaluated - matches Python's
conditional expression, and lets ``If(cond, safe, unsafe)`` guard the
``unsafe`` branch from firing when ``cond`` is truthy.

Sentinels: the condition or selector decides, so an ``EMPTY`` one never
passes (per ``nu.lang.sentinels``): ``If`` takes the else branch and
``Switch`` matches no key. The taken branch's value, ``EMPTY`` included,
passes through unchanged.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from nu.lang import ScalarQuery
from nu.lang.sentinels import EMPTY


if TYPE_CHECKING:
    from collections.abc import Callable, Mapping

    from nu.engine import Term
    from nu.lang.runtime import Runtime

__all__ = ["If", "Switch"]


class If(ScalarQuery):
    """The ``then`` branch if ``cond`` is truthy, else the ``else_`` branch.

    Args:
        cond: the condition to test.
        then: evaluated and yielded when ``cond`` is truthy.
        else_: evaluated and yielded when ``cond`` is falsy.

    Notes:
        - Short-circuits: only the taken branch is evaluated, matching
          Python's ``then if cond else else_``. This lets the untaken branch
          hold work that would fail or be unsafe to run.
        - Untyped: wrap it in the Form you want to keep working with, e.g.
          ``nu.Str(nu.If(c, "Admin", "Member")).upper()``.

    Yields:
        The taken branch's value. An EMPTY ``cond`` counts as false and
        takes ``else_``.

    Example:
        >>> nu.run(nu.If(True, "yes", "no"))[0]
        'yes'
        >>> nu.run(nu.If(False, "yes", "no"))[0]
        'no'
        >>> nu.run(nu.Str(nu.If(None, "Admin", "Member")).upper())[0]
        'MEMBER'
    """

    def _compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        cond, then_, else_ = children

        def thunk(rt: Runtime) -> object:
            return then_(rt) if cond(rt) else else_(rt)

        return thunk

    def _acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        cond, then_, else_ = children

        async def athunk(rt: Runtime) -> object:
            return await (then_(rt) if await cond(rt) else else_(rt))

        return athunk


class Switch(ScalarQuery):
    """The case value whose key matches the selector, or the default.

    Args:
        selector: the value to match against the case keys.
        cases: a mapping from key to case value.
        default: yielded when no key matches. Optional: leave it out to
            get EMPTY on no match instead.

    Notes:
        - The case keys are intrinsic constants, kept in the payload rather
          than as children, so they survive ``with_children`` unchanged.
        - Keys are matched by equality against the selector value, in the
          mapping's iteration order; the first match wins. An EMPTY
          selector matches no key.
        - Short-circuits: only the matching case value (or the default) is
          evaluated, not the others.
        - Sibling to the mutating ``nu.core.flows.control.SwitchDo``, which runs
          one of N bodies for effect instead of yielding a value.

    Yields:
        The matching case value, or the default when given and nothing
        matches. EMPTY when nothing matches and there is no default.

    Example:
        >>> nu.run(nu.Switch(2, {1: "one", 2: "two"}))[0]
        'two'
        >>> nu.run(nu.Switch(9, {1: "one", 2: "two"}, default="none"))[0]
        'none'
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

    def _compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        selector = children[0]
        values = children[1:]
        keys = self._payload["keys"]
        has_default = self._payload["has_default"]

        def thunk(rt: Runtime) -> object:
            s = selector(rt)
            if s is not EMPTY:
                for i, key in enumerate(keys):
                    if key == s:
                        return values[i](rt)
            if has_default:
                return values[-1](rt)
            return EMPTY

        return thunk

    def _acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        selector = children[0]
        values = children[1:]
        keys = self._payload["keys"]
        has_default = self._payload["has_default"]

        async def athunk(rt: Runtime) -> object:
            s = await selector(rt)
            if s is not EMPTY:
                for i, key in enumerate(keys):
                    if key == s:
                        return await values[i](rt)
            if has_default:
                return await values[-1](rt)
            return EMPTY

        return athunk
