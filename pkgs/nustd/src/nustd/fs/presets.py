"""mount() and tmp(): bind a directory as an fs mount for the span of a tree.

Both build a ``Provide`` over ``FsFabric``. Every option is a child of it,
so any one of them can be a term, computed when the bracket opens.

A temp dir's path is known only once it is made, so ``tmp`` also takes its
body as a lambda over the root: inside the mount a dynamic binding
(``nu.let``) evaluates the path and hands it to the lambda through a frame
of its own, the way ``nu.TryCatch`` hands its error. The path is a plain
``str``, so it travels where the mount cannot, such as to an ``nustd.mp``
worker as a value the body is given.
"""

from __future__ import annotations

import os
from typing import TYPE_CHECKING

from nu.context import Provide
from nu.lang import Literal, Nu
from nu.lang.binding import is_builder, lambda_params
from nu.mem import let

from .fabric import FsFabric, check_follow
from .refs import FsRef, check_tag


if TYPE_CHECKING:
    from collections.abc import Callable, Mapping


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
    return Provide(FsFabric, kwargs=options, body=body, tags=_tags(tag))


def tmp(
    *,
    tag: str | Nu | FsRef = "",
    prefix: str | Nu = "nu-",
    keep: bool | Nu = False,
    body: Nu | Callable[..., Nu] | None = None,
) -> Provide:
    """Mount a fresh temp dir for the body's duration, removed at exit.

    Args:
        tag: the tag to bind under, or the ``FsRef`` whose tag to use.
        prefix: the temp dir's name prefix.
        keep: leave the dir behind at exit; find it with ``ref.where()``.
        body: the tree that runs with the mount bound, or a lambda over the
            dir's absolute path (a mem ref) that builds it. A tree is handed
            no path.

    Notes:
        - Each run of the tree makes its own dir, in the system's temp dir.
        - The lambda runs once, at construction, and gets a ref to the path,
          not the path: it builds the body and never reads it in Python.
        - The path is a plain ``str``, evaluated inside the mount and held
          in the lambda's own frame for the body's span.
        - A lambda takes at most the one parameter; one taking none is a
          tree with no path.

    Yields:
        A ``Provide`` bracket binding the ``FsFabric``.

    Example:
        scratch = fs.FsRef()
        fs.tmp(body=nu.Sequential(scratch.write_text("a.txt", "hi"), scratch.copy("a.txt", "b.txt")))

        Handing the path to code outside the mount:

        fs.tmp(prefix="app-", body=lambda root: nu.print("working in", root))
    """
    options: Mapping[str, object] = {"temp": True, "prefix": prefix, "keep": keep}
    tags = _tags(tag)
    return Provide(FsFabric, kwargs=options, body=_rooted(body, tags), tags=tags)


def _rooted(body: object, tags: tuple[object, ...]) -> object:
    """``body``, a lambda over the mount's absolute path bound by a ``let`` inside it."""
    if not is_builder(body):
        return body
    params = lambda_params("fs.tmp", body)
    if len(params) > 1:
        msg = f"fs.tmp hands its body 1 value, so its lambda takes at most 1; got {len(params)}"
        raise TypeError(msg)
    where = FsRef(tags[0] if tags else "").where()
    return let(body, **dict.fromkeys(params, where))


def _tags(tag: object) -> tuple[object, ...]:
    """The binding's tags: none for ``""``, else the one tag, a term kept as given."""
    if isinstance(tag, FsRef):
        tag = tag.tag
        if isinstance(tag, Literal):
            tag = tag.value
    tag = check_tag(tag)
    return () if isinstance(tag, str) and not tag else (tag,)
