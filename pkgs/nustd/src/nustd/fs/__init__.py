r"""Nu fs fabric: a directory of the real file system, mounted for the span of a tree.

Every path is relative to its mount. One that would leave it (absolute, a
``..`` past the mount, a symlink the mount does not follow) raises
``FsEscape``, so a tree handed a mount reaches nothing else on the disk.

Surface:
    - FsRef(tag): a mount. Its queries are ``read_text``, ``read_bytes``,
      ``stat``, ``has``, ``usage``, ``where``, ``list``, ``open``, ``lines``
      and ``digest``; its writes are ``write_text``, ``write_bytes``,
      ``write_stream``, ``append``, ``append_stream``, ``mkdir``,
      ``remove``, ``remove_if_holds``, ``move``, ``copy``, ``touch`` and
      ``make_temp``; ``exists()`` asks whether a mount is bound.
    - FileRef: ``ref / "a"`` or ``ref.file("a")``, a path on a mount with
      the same verbs, the path filled in. A plain handle, not a term.
    - mount(path, tag=...), tmp(tag=...): bind a dir, or a fresh temp dir,
      as a mount for the span of a tree.
    - FsReadText, FsReadBytes, FsStat, FsHas, FsUsage, FsWhere, FsList,
      FsOpen, FsLines, FsDigest: the queries those terms build.
    - FsWriteText, FsWriteBytes, FsWriteStream, FsAppend, FsAppendStream,
      FsMkdir, FsRemove, FsRemoveIfHolds, FsMove, FsCopy, FsTouch,
      FsMakeTemp: the writes. Each lands on its mount's ``FsRef``, and a
      read only mount refuses them with ``FsReadOnly``.
    - FsFabric: the mount beneath them all.
    - FsEscape, FsReadOnly, FsLocked: what a mount raises beyond the
      built-in ``FileNotFoundError`` and friends.

A whole write goes through a temp file in the same dir, fsynced and moved
in place, so a reader sees the old bytes or the new ones, never half.

A sync run does the file work in place; an async run does it in a thread,
and a stream reads each piece in a thread.

Example::

    data = nustd.fs.FsRef("data")
    notes = data / "notes"

    app = nustd.fs.mount(
        "./data",
        tag="data",
        body=nu.Sequential(
            (notes / "today.md").write_text("# today\n"),
            nu.Collect(notes.list(pattern="*.md")),
        ),
    )
    entries = nu.run(app)[0]
"""

from __future__ import annotations

from .errors import FsEscape, FsLocked, FsReadOnly
from .fabric import STEP, FsFabric
from .interactions import (
    FsAppend,
    FsAppendStream,
    FsCopy,
    FsDigest,
    FsHas,
    FsLines,
    FsList,
    FsMakeTemp,
    FsMkdir,
    FsMove,
    FsOpen,
    FsReadBytes,
    FsReadText,
    FsRemove,
    FsRemoveIfHolds,
    FsStat,
    FsTouch,
    FsUsage,
    FsWhere,
    FsWriteBytes,
    FsWriteStream,
    FsWriteText,
)
from .presets import mount, tmp
from .refs import FileRef, FsRef


__all__ = [
    "STEP",
    "FileRef",
    "FsAppend",
    "FsAppendStream",
    "FsCopy",
    "FsDigest",
    "FsEscape",
    "FsFabric",
    "FsHas",
    "FsLines",
    "FsList",
    "FsLocked",
    "FsMakeTemp",
    "FsMkdir",
    "FsMove",
    "FsOpen",
    "FsReadBytes",
    "FsReadOnly",
    "FsReadText",
    "FsRef",
    "FsRemove",
    "FsRemoveIfHolds",
    "FsStat",
    "FsTouch",
    "FsUsage",
    "FsWhere",
    "FsWriteBytes",
    "FsWriteStream",
    "FsWriteText",
    "mount",
    "tmp",
]
