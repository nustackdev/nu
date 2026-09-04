"""What a consumer receives: one catalogue entry, per subject.

A record is a subject's name plus the two sources flattened for its kind.
Each kind defines its own, because they differ in what there is to say, and
they share this base.

The base carries what the format guarantees for every kind: a summary, an
optional description, notes and any examples. It is not a guess about what
kinds will have in common. Args and Yields are deliberately not here,
because whether a subject takes arguments or yields anything depends on the
kind.

Records are cheap. The prose is read at build time; the source text and the
raw docstring are fetched per lookup, so building a catalogue never touches
the filesystem.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any

from nu.inspect.core.contract import EXAMPLE, NOTES
from nu.inspect.core.docstring import Example, parse_examples, parse_notes, split_docstring
from nu.inspect.core.source import read_source


if TYPE_CHECKING:
    from nu.inspect.core.docstring import Blocks
    from nu.inspect.core.source import Source


__all__ = [
    "Record",
    "prose",
]


@dataclass(frozen=True)
class Record:
    """The base every kind's record shares."""

    name: str
    path: str
    summary: str = ""
    description: str = ""
    notes: tuple[str, ...] = ()
    examples: tuple[Example, ...] = ()
    target: object = field(default=None, repr=False, compare=False)

    @property
    def example(self) -> Example:
        """The first example, or an empty one when none was written.

        Convenience for callers that only ever want one example. Multi-example
        sections are still fully carried on :attr:`examples`.
        """
        return self.examples[0] if self.examples else Example()

    def blocks(self) -> Blocks:
        """The full docstring, split. Read per lookup, not at build."""
        return split_docstring(getattr(self.target, "__doc__", ""))

    def source(self) -> Source | None:
        """The source text and location. Read per lookup, not at build."""
        return read_source(self.target)


def prose(target: object, name: str, path: str, blocks: Blocks) -> dict[str, Any]:
    """The written half of a record, ready to splat into a kind's record.

    Args:
        target: the subject, kept for the per-lookup reads.
        name: what it is called.
        path: where it is reached, e.g. ``nu.core.Add``.
        blocks: its docstring, split.

    Returns:
        Keyword arguments for :class:`Record`'s own fields, alongside whatever
        the kind adds.
    """
    return {
        "name": name,
        "path": path,
        "target": target,
        "summary": blocks.summary,
        "description": blocks.description,
        "notes": parse_notes(blocks.text_of(*NOTES)),
        "examples": parse_examples(blocks.text_of(*EXAMPLE)),
    }
