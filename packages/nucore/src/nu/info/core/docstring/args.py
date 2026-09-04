"""The arguments a docstring documents.

What was written, and only that. Merging this with what the signature says is
a different question and belongs to the contract, not here.
"""

from __future__ import annotations

import re
from dataclasses import dataclass


__all__ = [
    "DocArg",
    "parse_args",
]

# "name: description", or "name (type): description", or "*children: ...".
_ITEM = re.compile(r"^(?P<name>\*{0,2}\w+)(?:\s*\([^)]*\))?:\s*(?P<text>.*)$")


@dataclass(frozen=True)
class DocArg:
    """One argument as the docstring describes it."""

    name: str
    text: str = ""
    variadic: bool = False


def parse_args(text: str) -> tuple[DocArg, ...]:
    """Parse an Args section into one entry per argument, in order.

    Continuation lines are folded into the argument above them, so a long
    description wraps without becoming a second argument.

    Args:
        text: the section body, already dedented.

    Returns:
        The documented arguments. Empty for empty text.
    """
    args: list[DocArg] = []
    parts: list[list[str]] = []
    for line in text.splitlines():
        item = _ITEM.match(line) if not line.startswith((" ", "\t")) else None
        if item is None:
            if parts:
                parts[-1].append(line.strip())
            continue
        name = item.group("name")
        args.append(DocArg(name=name.lstrip("*"), variadic=name.startswith("*")))
        parts.append([item.group("text")])
    return tuple(
        DocArg(name=arg.name, text=" ".join(p for p in bits if p), variadic=arg.variadic)
        for arg, bits in zip(args, parts, strict=True)
    )
