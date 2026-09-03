"""The sections the contract names, and the spellings tolerated for each.

One list, read by the guides, the checkers and the assemblers alike, so they
cannot disagree about what ``Args:`` is called.
"""

from __future__ import annotations


__all__ = [
    "ARGS",
    "EXAMPLE",
    "NOTES",
    "YIELDS",
]

ARGS = ("Args", "Arguments")
NOTES = ("Notes", "Note")
YIELDS = ("Yields", "Yield")
EXAMPLE = ("Example", "Examples")
