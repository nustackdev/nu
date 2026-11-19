"""mount() and tmp(): bind a directory as an fs mount for the span of a tree.

Both build a ``Provide`` over ``FsFabric``. Every option is a child of it,
so any one of them can be a term, computed when the bracket opens.
"""

from __future__ import annotations

import os
from typing import TYPE_CHECKING

from nu.context.fabric import Provide
from nu.lang import Literal, Nu

from .fabric import FsFabric, check_follow
from .refs import FsRef, check_tag


if TYPE_CHECKING:
    from collections.abc import Mapping


__all__ = ["mount", "tmp"]


def mount(
    path: str | os.PathLike[str] | Nu,
    *,
    tag: str | Nu | FsRef = "",
    readonly: bool | Nu = False,
    create: bool | Nu = True,
    mode: int | Nu | None = None,
    follow: str | Nu = "inside",
    body: Nu | None = None,
) -> Provide:
    """Mount the directory at ``path`` for the body's duration.

    Args:
        path: the directory. Relative paths resolve against the process's
            working dir when the bracket opens.
        tag: the tag to bind under, or the ``FsRef`` whose tag to use. ``""``
            binds the untagged mount ``FsRef()`` reads.
        readonly: refuse every write with ``FsReadOnly``.
        create: make the directory, with its parents, when it is missing.
        mode: permission bits for the directory when it is made.
        follow: the symlink rule, ``"inside"`` (default), ``"never"`` or
            ``"any"``; see ``FsFabric``.
        body: the tree that runs with the mount bound. Leave it out to use
            the preset inside a ``With``.

    Yields:
        A ``Provide`` bracket binding the ``FsFabric``.

    Example:
        data = fs.FsRef("data")
        nu.run(fs.mount("./data", tag="data", body=data.read_text("notes.md")))
    """
    if isinstance(follow, str):
        check_follow(follow)
    if not isinstance(path, Nu):
        path = os.fspath(path)
    options: Mapping[str, object] = {
        "path": path,
        "readonly": readonly,
        "create": create,
        "mode": mode,
        "follow": follow,
    }
    return Provide(FsFabric, options, body, tags=_tags(tag))


def tmp(
    *,
    tag: str | Nu | FsRef = "",
    prefix: str | Nu = "nu-",
    keep: bool | Nu = False,
    body: Nu | None = None,
) -> Provide:
    """Mount a fresh temp dir for the body's duration, removed at exit.

    Args:
        tag: the tag to bind under, or the ``FsRef`` whose tag to use.
        prefix: the temp dir's name prefix.
        keep: leave the dir behind at exit; find it with ``ref.where()``.
        body: the tree that runs with the mount bound.

    Notes:
        - Each run of the tree makes its own dir, in the system's temp dir.

    Yields:
        A ``Provide`` bracket binding the ``FsFabric``.

    Example:
        scratch = fs.FsRef()
        fs.tmp(body=nu.Sequential(scratch.write_text("a.txt", "hi"), scratch.read_text("a.txt")))
    """
    options: Mapping[str, object] = {"temp": True, "prefix": prefix, "keep": keep}
    return Provide(FsFabric, options, body, tags=_tags(tag))


def _tags(tag: object) -> tuple[object, ...]:
    """The binding's tags: none for ``""``, else the one tag, a term kept as given."""
    if isinstance(tag, FsRef):
        tag = tag.tag
        if isinstance(tag, Literal):
            tag = tag.value
    tag = check_tag(tag)
    return () if isinstance(tag, str) and not tag else (tag,)
