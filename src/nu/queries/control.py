"""Query-form branches -- If, Switch.

Single-yield Scalar Queries that evaluate a selector and return the
chosen branch's first value. For the imperative Command variants that
dispatch the branch's full stream, see
``nu.flows.control`` (IfDo, SwitchDo).
"""

from __future__ import annotations

from typing import Any, ClassVar

from nu.terms.query import ScalarQuery, _child_aeval, _child_eval
from nu.terms.types import Mode


__all__ = [
    "If",
    "Switch",
]


_BOTH = frozenset({Mode.SYNC, Mode.ASYNC})


class If(ScalarQuery):
    """Conditional Query. Children: [condition, then_branch, else_branch?]."""

    support: ClassVar[frozenset[Mode]] = _BOTH

    def __init__(
        self,
        condition: Any,  # noqa: ANN401
        then_branch: Any,  # noqa: ANN401
        else_branch: Any | None = None,  # noqa: ANN401
    ) -> None:
        if else_branch is None:
            super().__init__(condition, then_branch)
        else:
            super().__init__(condition, then_branch, else_branch)

    def eval(self, ctx: Any) -> Any:  # noqa: ANN401
        cond_v = _child_eval(self._children[0], ctx)
        if cond_v:
            return _child_eval(self._children[1], ctx)
        if len(self._children) > 2:
            return _child_eval(self._children[2], ctx)
        return None

    async def aeval(self, ctx: Any) -> Any:  # noqa: ANN401
        cond_v = await _child_aeval(self._children[0], ctx)
        if cond_v:
            return await _child_aeval(self._children[1], ctx)
        if len(self._children) > 2:
            return await _child_aeval(self._children[2], ctx)
        return None


class Switch(ScalarQuery):
    """Multi-way Query branching based on a selector value.

    Children: ``[selector, *case_values, default?]``
    """

    support: ClassVar[frozenset[Mode]] = _BOTH

    def __init__(
        self,
        selector: Any,  # noqa: ANN401
        cases: dict[Any, Any],
        default: Any | None = None,  # noqa: ANN401
    ) -> None:
        self._case_keys: list[Any] = list(cases.keys())
        self._has_default = default is not None
        children: list[Any] = [selector, *cases.values()]
        if default is not None:
            children.append(default)
        super().__init__(*children)

    def eval(self, ctx: Any) -> Any:  # noqa: ANN401
        value = _child_eval(self._children[0], ctx)
        for i, key in enumerate(self._case_keys):
            if key == value:
                return _child_eval(self._children[i + 1], ctx)
        if self._has_default:
            return _child_eval(self._children[-1], ctx)
        return None

    async def aeval(self, ctx: Any) -> Any:  # noqa: ANN401
        value = await _child_aeval(self._children[0], ctx)
        for i, key in enumerate(self._case_keys):
            if key == value:
                return await _child_aeval(self._children[i + 1], ctx)
        if self._has_default:
            return await _child_aeval(self._children[-1], ctx)
        return None
