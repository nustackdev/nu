"""Control Flow Commands -- While, DoWhile, Forever, SwitchDo.

Imperative branching/looping. Each evaluates conditions/selectors and
drives Command bodies. ``IfDo`` lives in ``nu.terms.flow`` (new-core);
re-exported here only for the package surface, NOT a separate class.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, ClassVar

from nu.terms.flow import Control
from nu.terms.types import Mode


if TYPE_CHECKING:
    from nu.terms import Nu


__all__ = [
    "DoWhile",
    "Forever",
    "SwitchDo",
    "While",
]


_BOTH = frozenset({Mode.SYNC, Mode.ASYNC})


class While(Control):
    """Loop while condition is truthy.

    Children: ``[condition, body]`` -- body is the Command at slot 1.
    """

    body_slots: ClassVar[tuple[int, ...]] = (1,)
    support: ClassVar[frozenset[Mode]] = _BOTH

    def __init__(self, condition: Any, body: Nu) -> None:  # noqa: ANN401
        super().__init__(condition, body)

    def run(self, ctx: Any) -> None:  # noqa: ANN401
        from nu import runtime

        cond_q = self._children[0]
        body = self._children[1]
        while runtime.first(cond_q, ctx):
            runtime.execute(body, ctx)

    async def arun(self, ctx: Any) -> None:  # noqa: ANN401
        from nu import runtime

        cond_q = self._children[0]
        body = self._children[1]
        while await runtime.afirst(cond_q, ctx):
            await runtime.aexecute(body, ctx)


class DoWhile(Control):
    """Execute body first, then loop while condition is truthy.

    Children: ``[body, condition]`` -- body is the Command at slot 0.
    """

    body_slots: ClassVar[tuple[int, ...]] = (0,)
    support: ClassVar[frozenset[Mode]] = _BOTH

    def __init__(self, condition: Any, body: Nu) -> None:  # noqa: ANN401
        # Body in slot 0, condition in slot 1 to satisfy body_slots invariants.
        super().__init__(body, condition)

    def run(self, ctx: Any) -> None:  # noqa: ANN401
        from nu import runtime

        body = self._children[0]
        cond_q = self._children[1]
        runtime.execute(body, ctx)
        while runtime.first(cond_q, ctx):
            runtime.execute(body, ctx)

    async def arun(self, ctx: Any) -> None:  # noqa: ANN401
        from nu import runtime

        body = self._children[0]
        cond_q = self._children[1]
        await runtime.aexecute(body, ctx)
        while await runtime.afirst(cond_q, ctx):
            await runtime.aexecute(body, ctx)


class Forever(Control):
    """Execute body indefinitely.

    Children: ``[body]``
    """

    body_slots: ClassVar[tuple[int, ...]] = (0,)
    support: ClassVar[frozenset[Mode]] = _BOTH

    def __init__(self, body: Nu) -> None:
        super().__init__(body)

    def run(self, ctx: Any) -> None:  # noqa: ANN401
        from nu import runtime

        body = self._children[0]
        while True:
            runtime.execute(body, ctx)

    async def arun(self, ctx: Any) -> None:  # noqa: ANN401
        from nu import runtime

        body = self._children[0]
        while True:
            await runtime.aexecute(body, ctx)


class SwitchDo(Control):
    """Multi-way branching based on a selector value.

    Children: ``[selector, *case_bodies, default?]``

    Selector is at slot 0 (Query). All other slots are Command bodies
    (case branches and the optional default branch).
    """

    support: ClassVar[frozenset[Mode]] = _BOTH

    def __init__(
        self,
        selector: Any,  # noqa: ANN401
        cases: dict[Any, Nu],
        default: Nu | None = None,
    ) -> None:
        self._case_keys: list[Any] = list(cases.keys())
        self._has_default = default is not None

        children: list = [selector, *cases.values()]
        if default is not None:
            children.append(default)
        super().__init__(*children)

    # body_slots covers every slot except 0 (the selector). Wide range so
    # any number of cases is within scope; trichotomy only inspects slots
    # that actually have children.
    body_slots: ClassVar[tuple[int, ...]] = tuple(range(1, 1024))

    def run(self, ctx: Any) -> None:  # noqa: ANN401
        from nu import runtime

        value = runtime.first(self._children[0], ctx)
        for i, key in enumerate(self._case_keys):
            if key == value:
                runtime.execute(self._children[i + 1], ctx)
                return
        if self._has_default:
            runtime.execute(self._children[-1], ctx)

    async def arun(self, ctx: Any) -> None:  # noqa: ANN401
        from nu import runtime

        value = await runtime.afirst(self._children[0], ctx)
        for i, key in enumerate(self._case_keys):
            if key == value:
                await runtime.aexecute(self._children[i + 1], ctx)
                return
        if self._has_default:
            await runtime.aexecute(self._children[-1], ctx)
