"""The laws every kind shares: what a docstring may not lie about.

A violation is a written fact that contradicts the code, or a section written
in a form the format does not allow. A missing section is not a violation: it
is absence, already carried by the record as an empty field, and the
consumer decides whether to care.

Each check returns violations and never raises. A kind composes the checks
its subject can be held to and adds its own.

Where a rule cannot be decided the subject is left alone rather than flagged.
These run over the whole stack at once, so a false positive costs more than a
miss: it sends someone to rewrite a docstring that was already right.
"""

from __future__ import annotations

import ast
from dataclasses import dataclass
from typing import TYPE_CHECKING

from nu.info.core.contract.sections import ARGS, EXAMPLE
from nu.info.core.docstring import parse_args, parse_example


if TYPE_CHECKING:
    from nu.info.core.docstring import Blocks


__all__ = [
    "SUMMARY_LIMIT",
    "Violation",
    "check_args",
    "check_example",
    "check_summary",
]

SUMMARY_LIMIT = 88


@dataclass(frozen=True)
class Violation:
    """One written fact that contradicts the code, or a malformed section."""

    subject: str
    rule: str
    detail: str = ""


def check_summary(subject: str, blocks: Blocks) -> list[Violation]:
    """A summary that is present must be one line, ending in a period."""
    if not blocks.summary:
        return []
    violations: list[Violation] = []
    if not blocks.summary.endswith("."):
        violations.append(
            Violation(subject=subject, rule="summary-unterminated", detail=blocks.summary)
        )
    if len(blocks.summary) > SUMMARY_LIMIT:
        violations.append(
            Violation(subject=subject, rule="summary-too-long", detail=str(len(blocks.summary)))
        )
    return violations


def check_args(subject: str, blocks: Blocks, expected: int | None) -> list[Violation]:
    """An Args section that is present must agree with the code's arity.

    A docstring that documents three arguments for a two-argument thing reads
    as authoritative and is unrecoverable for anyone following it, because the
    truth is nowhere in the text. Absence is not a violation and is not
    checked here.
    """
    documented = parse_args(blocks.text_of(*ARGS))
    if not documented or any(arg.variadic for arg in documented):
        return []
    if expected is not None and expected != len(documented):
        return [
            Violation(
                subject=subject,
                rule="args-arity-mismatch",
                detail=f"documents {len(documented)}, code takes {expected}",
            )
        ]
    return []


def check_example(subject: str, blocks: Blocks) -> list[Violation]:
    """An Example section that is present must be parseable and honest.

    Absence is not a violation; a written example that cannot be run, or that
    claims a value it does not produce, is.
    """
    text = blocks.text_of(*EXAMPLE)
    if not text.strip():
        return []
    example = parse_example(text)
    if not example:
        return [Violation(subject=subject, rule="example-empty")]
    try:
        ast.parse(example.code)
    except SyntaxError as err:
        return [Violation(subject=subject, rule="example-unparseable", detail=str(err.msg))]
    if example.doctest and not example.expected:
        return [Violation(subject=subject, rule="example-no-value")]
    return []
