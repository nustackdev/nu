"""Nu's gates: validity rules over a compiled program.

A gate rule reads the attributes compilation produced and yields a Violation
per breach. None of them mutate the program; a verdict is returned, and
``validate`` is the layer where a non-empty verdict becomes a rejection.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from nu.engine import Violation
from nu.symbols.sorts import MATRIX, Effect, own_label, subsort


if TYPE_CHECKING:
    from collections.abc import Iterator

    from nu.engine import Program
    from nu.engine.program import Path

__all__ = [
    "RULES",
    "rule_command_has_write",
    "rule_composition",
    "rule_flow_has_command",
    "rule_query_no_write",
    "rule_ref_slots",
    "rule_refused",
]


def _child_label(program: Program, path: Path) -> str | None:
    """The matrix label a parent sees for a child, looking through Spans."""
    sort = program.attr(path, "sort")
    if subsort(sort, "Span"):
        kids = program.children(path)
        return _child_label(program, kids[0]) if kids else own_label(sort)
    return own_label(sort)


def rule_composition(program: Program, path: Path) -> Iterator[Violation]:
    """Every child must be accepted by the composition matrix."""
    parent = own_label(program.attr(path, "sort"))
    if parent is None:
        return
    for child in program.children(path):
        label = _child_label(program, child)
        if label is not None and label not in MATRIX[parent]:
            yield Violation(path, "COMPOSE", f"{parent} cannot hold {label}")


def rule_query_no_write(program: Program, path: Path) -> Iterator[Violation]:
    """A Query subtree must never contain a WRITE."""
    if not subsort(program.attr(path, "sort"), "Query"):
        return
    if any(eff is Effect.WRITE for _, eff in program.attr(path, "tracked_effects")):
        yield Violation(path, "QUERY_WRITE", "Query subtree contains a WRITE")


def rule_command_has_write(program: Program, path: Path) -> Iterator[Violation]:
    """A Command must declare at least one WRITE slot."""
    if not subsort(program.attr(path, "sort"), "Command"):
        return
    if Effect.WRITE not in program.attr(path, "own_effects").values():
        yield Violation(path, "CMD_WRITE", "Command declares no WRITE slot")


def rule_flow_has_command(program: Program, path: Path) -> Iterator[Violation]:
    """A Flow subtree must contain at least one Command."""
    if not subsort(program.attr(path, "sort"), "Flow"):
        return
    for node in program.walk(path):
        if subsort(program.attr(node, "sort"), "Command"):
            return
    yield Violation(path, "FLOW_EMPTY", "Flow subtree contains no Command")


def rule_refused(program: Program, path: Path) -> Iterator[Violation]:
    """A scalar consumer cannot be fed a stream without a reduction."""
    if program.attr(path, "realization") != "scalar":
        return
    if program.attr(path, "is_reduction"):
        return
    for child in program.children(path):
        if program.attr(child, "realization_eff") == "stream":
            yield Violation(path, "REFUSED", "scalar consumer fed a stream")


def rule_ref_slots(program: Program, path: Path) -> Iterator[Violation]:
    """A slot declared in own_effects must hold a Ref."""
    kids = program.children(path)
    for slot in program.attr(path, "own_effects"):
        if slot < len(kids) and program.attr(kids[slot], "sort") != "Ref":
            yield Violation(path, "SLOT", f"slot {slot} must hold a Ref")


RULES = (
    rule_composition,
    rule_query_no_write,
    rule_command_has_write,
    rule_flow_has_command,
    rule_refused,
    rule_ref_slots,
)
