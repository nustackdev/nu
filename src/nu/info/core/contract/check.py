"""The checks every kind shares, one per section of the contract.

Each returns problems and never raises: a non-conformant thing is data, and
the point of the checker is to be run across a package and counted. A kind
composes the checks its guide requires and adds its own.

Where a rule cannot be decided the subject is left alone rather than flagged.
These run over the whole stack at once, so a false positive costs more than a
miss: it sends someone to rewrite a docstring that was already right.
"""

from __future__ import annotations

import ast
from dataclasses import dataclass
from typing import TYPE_CHECKING

from nu.info.core.contract.sections import ARGS, EXAMPLE, YIELDS
from nu.info.core.docstring import parse_args, parse_example


if TYPE_CHECKING:
    from nu.info.core.docstring import Blocks


__all__ = [
    "SUMMARY_LIMIT",
    "Problem",
    "check_args",
    "check_example",
    "check_summary",
    "check_yields",
]

SUMMARY_LIMIT = 88


@dataclass(frozen=True)
class Problem:
    """One way a subject diverges from the contract."""

    subject: str
    rule: str
    detail: str = ""


def check_summary(subject: str, blocks: Blocks) -> list[Problem]:
    """One line, one sentence, ending in a period, and not a paragraph."""
    if not blocks.summary:
        return [Problem(subject=subject, rule="summary-missing")]
    problems: list[Problem] = []
    if not blocks.summary.endswith("."):
        problems.append(
            Problem(subject=subject, rule="summary-unterminated", detail=blocks.summary)
        )
    if len(blocks.summary) > SUMMARY_LIMIT:
        problems.append(
            Problem(subject=subject, rule="summary-too-long", detail=str(len(blocks.summary)))
        )
    return problems


def check_args(subject: str, blocks: Blocks, expected: int | None) -> list[Problem]:
    """Args present, and agreeing with what the code says it takes.

    The agreement check is the reason Args is required at all. A docstring
    that documents three arguments for a two-argument thing reads as
    authoritative and is unrecoverable for anyone following it, because the
    truth is nowhere in the text.

    Args:
        subject: what to name in a problem.
        blocks: the split docstring.
        expected: how many arguments the code says there are, or None when
            that cannot be read.

    Returns:
        The problems found.
    """
    documented = parse_args(blocks.text_of(*ARGS))
    if not documented:
        # Only a subject provably taking nothing is excused. An unreadable
        # count is treated as "probably takes arguments", because most do.
        return [] if expected == 0 else [Problem(subject=subject, rule="args-missing")]
    if any(arg.variadic for arg in documented):
        return []
    if expected is not None and expected != len(documented):
        return [
            Problem(
                subject=subject,
                rule="args-arity-mismatch",
                detail=f"documents {len(documented)}, code takes {expected}",
            )
        ]
    return []


def check_yields(subject: str, blocks: Blocks) -> list[Problem]:
    """A Yields section, saying what evaluating the subject produces."""
    if not blocks.text_of(*YIELDS).strip():
        return [Problem(subject=subject, rule="yields-missing")]
    return []


def check_example(subject: str, blocks: Blocks) -> list[Problem]:
    """One example, parseable, and carrying the value it produces."""
    text = blocks.text_of(*EXAMPLE)
    if not text.strip():
        return [Problem(subject=subject, rule="example-missing")]
    example = parse_example(text)
    if not example:
        return [Problem(subject=subject, rule="example-empty")]
    try:
        ast.parse(example.code)
    except SyntaxError as err:
        return [Problem(subject=subject, rule="example-unparseable", detail=str(err.msg))]
    if not example.doctest:
        return [Problem(subject=subject, rule="example-not-doctest")]
    if not example.expected:
        return [Problem(subject=subject, rule="example-no-value")]
    return []
