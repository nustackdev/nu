"""What was written: a docstring, parsed.

One module per thing a docstring holds, each with its parser and the value
that parser produces. Generic Google-style parsing throughout: which sections
matter and which are required is the contract's business, not this layer's.

- ``blocks`` splits a docstring into summary, description and named sections.
  Summary and description come out of the split because they are defined by
  position, so they have no readers of their own.
- ``args`` parses an Args section into one entry per argument.
- ``notes`` parses a Notes section into one string per bullet.
- ``example`` parses an Example section into code and its expected value.

A Yields section is free text, so it needs no reader: it is read straight off
the blocks.
"""

from __future__ import annotations

from nu.inspect.core.docstring.args import DocArg, parse_args
from nu.inspect.core.docstring.blocks import Blocks, Section, split_docstring
from nu.inspect.core.docstring.example import Example, parse_example, parse_examples
from nu.inspect.core.docstring.notes import parse_notes


__all__ = [
    "Blocks",
    "DocArg",
    "Example",
    "Section",
    "parse_args",
    "parse_example",
    "parse_examples",
    "parse_notes",
    "split_docstring",
]
