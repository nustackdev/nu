"""Split a docstring into its blocks. The step every other reader starts from.

A docstring is a summary line, a description, and named sections. Splitting it
is generic Google-style parsing and knows nothing about which sections matter,
which is the contract's business.

Summary and description come out of the split itself rather than from their
own readers, because they are defined by position: the first line, and
everything before the first section header.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from textwrap import dedent


__all__ = [
    "Blocks",
    "Section",
    "split_docstring",
]

# A section header: an optionally indented capitalised word, then a colon,
# alone on its line. "Args:", "Yields:", "Example:" match; "Note: see below"
# does not, because the line carries text after the colon.
_HEADER = re.compile(r"^(?P<indent>[ \t]*)(?P<name>[A-Z][A-Za-z ]{0,20}):[ \t]*$")


@dataclass(frozen=True)
class Section:
    """One named section, as raw dedented text."""

    name: str
    text: str


@dataclass(frozen=True)
class Blocks:
    """A docstring split into summary, description and named sections."""

    raw: str = ""
    summary: str = ""
    description: str = ""
    sections: tuple[Section, ...] = ()

    def section(self, *names: str) -> Section | None:
        """The first section matching any of ``names``, or None."""
        wanted = {name.lower() for name in names}
        for section in self.sections:
            if section.name.lower() in wanted:
                return section
        return None

    def text_of(self, *names: str) -> str:
        """The text of the first section matching any of ``names``, or empty."""
        section = self.section(*names)
        return section.text if section is not None else ""


def split_docstring(text: str | None) -> Blocks:
    """Split ``text`` into summary, description and sections.

    An empty or missing docstring splits to empty Blocks rather than raising,
    so a caller can treat absence as data.

    Args:
        text: the raw docstring, or None.

    Returns:
        The blocks, with the raw text kept. Everything a consumer wants that
        is not the summary or the description is reached through
        :meth:`Blocks.section`.
    """
    if not text or not text.strip():
        return Blocks(raw=text or "")
    clean = dedent(text.strip("\n")).strip()
    lines = clean.splitlines()
    rest = lines[1:]
    description: list[str] = []
    sections: list[Section] = []
    index = 0
    while index < len(rest):
        header = _HEADER.match(rest[index])
        if header is None:
            description.append(rest[index])
            index += 1
            continue
        index += 1
        body, index = _take(rest, index, len(header.group("indent")))
        sections.append(Section(name=header.group("name").strip(), text=body))
    return Blocks(
        raw=text,
        summary=lines[0].strip(),
        description="\n".join(description).strip(),
        sections=tuple(sections),
    )


def _take(lines: list[str], start: int, indent: int) -> tuple[str, int]:
    """Collect the lines indented under a header, and the index after them."""
    taken: list[str] = []
    index = start
    while index < len(lines):
        line = lines[index]
        if line.strip() and len(line) - len(line.lstrip()) <= indent:
            break
        taken.append(line)
        index += 1
    while taken and not taken[-1].strip():
        taken.pop()
    return dedent("\n".join(taken)).strip("\n"), index
