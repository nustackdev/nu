"""Control flow primitives.

This module provides basic control flow structures:
- Sequence/Seq: Execute children in order
- If: Conditional execution
- While: Loop while condition is true
- Forever: Infinite loop (until cancelled)
- Switch: Multi-way branching
- DoWhile: Loop at least once, then check condition
"""

from __future__ import annotations

from typing import Any

import attrs

from everyabc import Flow, Runtime, Term


__all__ = [
    "DoWhile",
    "Forever",
    "If",
    "Seq",
    "Sequence",
    "Switch",
    "While",
]


@attrs.define
class _Sequence[RuntimeT: Runtime](Flow[RuntimeT]):
    """Execute children in order."""

    children: Flow | Term | list[Flow | Term] = attrs.field(factory=list)

    async def run(self, runtime: RuntimeT) -> None:
        """Execute children sequentially."""
        children = self.children if isinstance(self.children, list) else [self.children]

        for i, child in enumerate(children):
            # runtime.cancellation.terminate_cancelled(runtime.path)
            await self.execute_child(child, i, runtime)


@attrs.define
class _While[RuntimeT: Runtime](Flow[RuntimeT]):
    """Execute child while condition is true."""

    condition: Term | bool = attrs.field(default=False)
    child: Flow | Term | None = attrs.field(default=None)

    async def run(self, runtime: RuntimeT) -> None:
        """Execute child while condition holds."""
        if not self.child:
            raise ValueError("No child is provided")

        while True:
            runtime.cancellation.terminate_cancelled(runtime.path)

            if isinstance(self.condition, Term):
                condition = runtime.terms.execute_term(self.condition)
            else:
                condition = self.condition

            if not condition:
                break

            await self.execute_child(self.child, 0, runtime)


@attrs.define
class _DoWhile[RuntimeT: Runtime](Flow[RuntimeT]):
    """Execute child at least once, then continue while condition is true.

    Unlike While, DoWhile always executes the child at least once
    before checking the condition.

    Flow Building Pattern:
        DoWhile is useful when you need to perform an action at least
        once regardless of the condition (e.g., menu display, prompt).
    """

    condition: Term | bool = attrs.field(default=False)
    child: Flow | Term | None = attrs.field(default=None)

    async def run(self, runtime: RuntimeT) -> None:
        """Execute child, then loop while condition holds."""
        if not self.child:
            raise ValueError("No child is provided")

        while True:
            runtime.cancellation.terminate_cancelled(runtime.path)

            # Execute first, then check condition
            await self.execute_child(self.child, 0, runtime)

            if isinstance(self.condition, Term):
                condition = runtime.terms.execute_term(self.condition)
            else:
                condition = self.condition

            if not condition:
                break


@attrs.define
class _If[RuntimeT: Runtime](Flow[RuntimeT]):
    """Execute child conditionally."""

    condition: Term | bool = attrs.field(default=False)
    child: Flow | Term | None = attrs.field(default=None)
    else_child: Flow | Term | None = attrs.field(default=None)

    async def run(self, runtime: RuntimeT) -> None:
        """Execute child if condition is true, else_child otherwise."""
        if not self.child:
            raise ValueError("No child is provided")

        if isinstance(self.condition, Term):
            condition = runtime.terms.execute_term(self.condition)
        else:
            condition = self.condition

        if bool(condition):
            await self.execute_child(self.child, 0, runtime)
        else:
            if self.else_child is not None:
                await self.execute_child(self.else_child, "else", runtime)


@attrs.define
class _Switch[RuntimeT: Runtime](Flow[RuntimeT]):
    """Multi-way branching based on a value.

    Evaluates the selector and executes the matching case.
    Falls back to default if no case matches.

    Flow Building Pattern:
        Switch provides cleaner multi-way branching than nested If flows.
        Cases are matched by equality. The matched case key is available
        via runtime.attributes as "case".

    Example use cases:
        - State machine transitions
        - Command dispatch
        - Status-based routing
    """

    selector: Term | Any = attrs.field(default=None)
    cases: dict[Any, Flow | Term] = attrs.field(factory=dict)
    default: Flow | Term | None = attrs.field(default=None)
    name: str | None = attrs.field(default=None)

    async def run(self, runtime: RuntimeT) -> None:
        """Execute matching case or default."""
        if isinstance(self.selector, Term):
            value = runtime.terms.execute_term(self.selector)
        else:
            value = self.selector

        # Find matching case
        if value in self.cases:
            # Store matched case for child access (if serializable)
            # Store as string representation for safety
            runtime.attributes.set(
                runtime.path,
                "case",
                str(value) if value is not None else None,
                step_name=self.name,
            )
            await self.execute_child(self.cases[value], f"case_{value}", runtime)
        elif self.default is not None:
            await self.execute_child(self.default, "default", runtime)


# =============================================================================
# Wrapper Functions
# =============================================================================


def Sequence(*children: Flow | Term) -> _Sequence:  # noqa: N802
    """Execute children in order.

    Args:
        *children: Child flows to execute sequentially

    Returns:
        Sequence flow

    Example:
        >>> Sequence(Print("Hello"), Delay(1), Print("World"))
    """
    return _Sequence(children=list(children))


def Seq(*children: Flow | Term) -> _Sequence:  # noqa: N802
    """Shorthand for Sequence - execute children in order.

    Args:
        *children: Child flows to execute sequentially

    Returns:
        Sequence flow

    Example:
        >>> Seq(Print("Hello"), Delay(1), Print("World"))
    """
    return _Sequence(children=list(children))


def While(cond: Term | bool, child: Flow | Term) -> _While:  # noqa: N802
    """Execute child while condition is true.

    Args:
        cond: Condition to evaluate (Term or bool)
        child: Child flow to execute while condition is true

    Returns:
        While flow

    Example:
        >>> While(counter.get() < 10, Increment(counter))
    """
    return _While(condition=cond, child=child)


def DoWhile(cond: Term | bool, child: Flow | Term) -> _DoWhile:  # noqa: N802
    """Execute child at least once, then continue while condition is true.

    Unlike While, DoWhile always executes once before checking condition.

    Args:
        cond: Condition to evaluate after each execution
        child: Child flow to execute

    Returns:
        DoWhile flow

    Example:
        >>> DoWhile(has_more.get(), FetchNextPage())
    """
    return _DoWhile(condition=cond, child=child)


def Forever(child: Flow | Term) -> _While:  # noqa: N802
    """Execute child forever (unless cancelled or terminated externally).

    Args:
        child: Child flow to execute indefinitely

    Returns:
        While flow with hardcoded `True` condition

    Example:
        >>> Forever(ProcessMessages())
    """
    return _While(condition=True, child=child)


def If(  # noqa: N802
    cond: Term | bool,
    child: Flow | Term,
    otherwise: Flow | Term | None = None,
) -> _If:
    """Execute child conditionally.

    Args:
        cond: Condition to evaluate (Term or bool)
        child: Child flow to execute if condition is true
        otherwise: Optional child flow to execute if condition is false

    Returns:
        If flow

    Example:
        >>> If(slots.length() > 0, ProcessSlots(), Delay(0.1))
    """
    return _If(condition=cond, child=child, else_child=otherwise)


def Switch(  # noqa: N802
    selector: Term | Any,
    cases: dict[Any, Flow | Term],
    default: Flow | Term | None = None,
) -> _Switch:
    """Multi-way branching based on a value.

    Evaluates selector and executes the matching case.
    Matched case available via runtime.attributes as "case".

    Args:
        selector: Value to match against cases (Term or Hashable)
        cases: Dict mapping values to flows
        default: Flow to execute if no case matches

    Returns:
        Switch flow

    Example:
        >>> Switch(
        ...     status.get(),
        ...     cases={
        ...         "pending": HandlePending(),
        ...         "active": HandleActive(),
        ...         "done": HandleDone(),
        ...     },
        ...     default=HandleUnknown(),
        ... )
    """
    return _Switch(selector=selector, cases=cases, default=default)
