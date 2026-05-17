"""Metaprogramming: processes over a compiled program. None of them mutate it.

A gate runs validity rules over every node and returns a verdict. validate
turns a non-empty verdict into a rejection. The verdict is returned to the
caller, never stored on the program.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, NamedTuple


if TYPE_CHECKING:
    from collections.abc import Callable, Iterable

    from nu.engine.program import Path, Program

__all__ = ["Rule", "Violation", "gate", "validate"]


class Violation(NamedTuple):
    """One rule failure: where it is, which rule, and why."""

    path: Path
    rule: str
    detail: str


type Rule = Callable[[Program, Path], Iterable[Violation]]


def gate(program: Program, *rules: Rule) -> list[Violation]:
    """Run each rule over every node and return every violation found.

    The verdict is returned, never written onto the program.
    """
    return [
        violation for path in program.walk() for rule in rules for violation in rule(program, path)
    ]


def validate(program: Program, *rules: Rule) -> Program:
    """Run a gate; raise if the verdict is non-empty, else return the program.

    Raises:
        ValueError: if any rule yields a violation.
    """
    verdict = gate(program, *rules)
    if verdict:
        lines = "\n".join(f"  [{v.rule}] {v.detail}  at {v.path}" for v in verdict)
        raise ValueError(f"invalid program:\n{lines}")
    return program
