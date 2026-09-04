"""Source reading: an object in, its source text and location out.

Every call here touches the filesystem, so nothing in a catalogue may call
it eagerly. Records reach for it per lookup, never per build. Objects with
no readable source (builtins, dynamically built classes) come back as None.
"""

from __future__ import annotations

import inspect
from dataclasses import dataclass


__all__ = [
    "Source",
    "read_location",
    "read_source",
]


@dataclass(frozen=True)
class Source:
    """The source text of an object, and where it came from."""

    text: str
    file: str = ""
    line: int = 0


def read_source(target: object) -> Source | None:
    """The source of ``target``, or None when there is none to read."""
    location = read_location(target)
    try:
        text = inspect.getsource(target)  # type: ignore[arg-type]
    except (OSError, TypeError):
        return None
    if location is None:
        return Source(text=text)
    return Source(text=text, file=location[0], line=location[1])


def read_location(target: object) -> tuple[str, int] | None:
    """The file and first line of ``target``, or None when unknown."""
    try:
        file = inspect.getsourcefile(target)  # type: ignore[arg-type]
        _, line = inspect.getsourcelines(target)  # type: ignore[arg-type]
    except (OSError, TypeError):
        return None
    if file is None:
        return None
    return file, line
