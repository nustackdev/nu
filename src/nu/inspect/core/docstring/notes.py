"""The bullets a Notes section holds, one discrete fact each."""

from __future__ import annotations


__all__ = ["parse_notes"]


def parse_notes(text: str) -> tuple[str, ...]:
    """Split a Notes section into one string per bullet.

    Continuation lines fold into the bullet above them. Content with no bullet
    marker at all comes back as a single entry, so a prose Notes section is
    not silently dropped.

    Args:
        text: the section body, already dedented.

    Returns:
        One string per note, in order. Empty for empty text.
    """
    notes: list[list[str]] = []
    for line in text.splitlines():
        stripped = line.strip()
        if not stripped:
            continue
        if stripped.startswith(("- ", "* ")):
            notes.append([stripped[2:].strip()])
        elif notes:
            notes[-1].append(stripped)
        else:
            notes.append([stripped])
    return tuple(" ".join(parts) for parts in notes)
