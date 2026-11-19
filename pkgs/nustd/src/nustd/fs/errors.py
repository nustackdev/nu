"""What the fs fabric raises beyond the built-ins.

A missing file is ``FileNotFoundError``, a taken name ``FileExistsError``, a
dir where a file was asked for ``IsADirectoryError`` and the other way
``NotADirectoryError``: the built-ins, as ``os`` raises them. The three here
are the states only a mount has.
"""

from __future__ import annotations


__all__ = ["FsEscape", "FsLocked", "FsReadOnly"]


class FsEscape(PermissionError):  # noqa: N818 - a state, not an error kind
    """A path that would leave its mount.

    An absolute path, a ``..`` climbing past the mount, or a symlink the
    mount's ``follow`` rule does not allow.
    """


class FsReadOnly(PermissionError):  # noqa: N818 - a state, not an error kind
    """A write on a mount bound with ``readonly=True``."""


class FsLocked(BlockingIOError):  # noqa: N818 - a state, not an error kind
    """A lock another holder has.

    Args:
        message: what was refused, and who holds it.
        holder: the holder's record, ``{host, pid, what, taken_at}``, or an
            empty dict when the lock file says nothing.
    """

    def __init__(self, message: str, holder: dict[str, object] | None = None) -> None:
        super().__init__(message)
        self.holder: dict[str, object] = dict(holder or {})

    def __reduce__(self) -> tuple[type[FsLocked], tuple[str, dict[str, object]]]:
        return (FsLocked, (str(self.args[0]) if self.args else "", self.holder))
