"""Nu fs fabric: a directory of the real file system, mounted for the span of a tree.

Every path is relative to its mount. One that would leave it (absolute, a
``..`` past the mount, a symlink the mount does not follow) raises
``FsEscape``, so a tree handed a mount reaches nothing else on the disk.

Surface:
    - FsRef(tag): a mount; its terms are ``read_text``, ``read_bytes``,
      ``stat``, ``has``, ``usage``, ``where``, ``list``, ``open``, ``lines``
      and ``digest``, and ``exists()`` asks whether a mount is bound.
    - FileRef: ``ref / "a"`` or ``ref.file("a")``, a path on a mount with
      the same verbs, the path filled in. A plain handle, not a term.
    - mount(path, tag=...), tmp(tag=...): bind a dir, or a fresh temp dir,
      as a mount for the span of a tree.
    - FsReadText, FsReadBytes, FsStat, FsHas, FsUsage, FsWhere, FsList,
      FsOpen, FsLines, FsDigest: the interactions those terms build;
      FsFabric beneath them.
    - FsEscape, FsReadOnly, FsLocked: what a mount raises beyond the
      built-in ``FileNotFoundError`` and friends.

A sync run does the file work in place; an async run does it in a thread,
and a stream reads each piece in a thread.

Example::

    data = nustd.fs.FsRef("data")
    notes = data / "notes"

    app = nustd.fs.mount(
        "./data",
        tag="data",
        body=nu.Collect(notes.list(pattern="*.md")),
    )
    entries = nu.run(app)[0]
"""

from __future__ import annotations

from .errors import FsEscape, FsLocked, FsReadOnly
from .fabric import STEP, FsFabric
from .interactions import (
    FsDigest,
    FsHas,
    FsLines,
    FsList,
    FsOpen,
    FsReadBytes,
    FsReadText,
    FsStat,
    FsUsage,
    FsWhere,
)
from .presets import mount, tmp
from .refs import FileRef, FsRef


__all__ = [
    "STEP",
    "FileRef",
    "FsDigest",
    "FsEscape",
    "FsFabric",
    "FsHas",
    "FsLines",
    "FsList",
    "FsLocked",
    "FsOpen",
    "FsReadBytes",
    "FsReadOnly",
    "FsReadText",
    "FsRef",
    "FsStat",
    "FsUsage",
    "FsWhere",
    "mount",
    "tmp",
]
