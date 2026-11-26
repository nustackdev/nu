"""mount() and tmp(): bind a directory as an fs mount for the span of a tree.

Both build a ``Provide`` over ``FsFabric``. Every option is a child of it,
so any one of them can be a term, computed when the bracket opens.

A temp dir's path is known only once it is made, so ``tmp`` also takes its
body as a lambda over the root: the path lands in ``ctx.attrs`` under a
name the lambda owns, the way ``nu.TryCatch`` hands its error. A plain
string in the attrs travels where the mount cannot, such as to an
``nustd.mp`` worker through ``Teleport(..., carry=True)``.
"""

from __future__ import annotations

import os
from contextlib import contextmanager
from typing import TYPE_CHECKING

from nu.context.attrs.binders import bind
from nu.context.fabric import Provide
from nu.lang import Bracket, Literal, Nu

from .fabric import FsFabric, check_follow
from .refs import FsRef, check_tag


if TYPE_CHECKING:
    from collections.abc import Callable, Iterator, Mapping

    from nu.lang.runtime import Context


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
    root_key: str | None = None,
    body: Nu | Callable[[Nu], Nu] | None = None,
) -> Provide:
    """Mount a fresh temp dir for the body's duration, removed at exit.

    Args:
        tag: the tag to bind under, or the ``FsRef`` whose tag to use.
        prefix: the temp dir's name prefix.
        keep: leave the dir behind at exit; find it with ``ref.where()``.
        root_key: where the dir's absolute path lands in ``ctx.attrs`` for
            a tree body to read with ``nu.Attr``. Left out, a tree body is
            handed no path; a lambda mints its own name.
        body: the tree that runs with the mount bound, or a lambda over the
            dir's absolute path (a ``nu.Attr``) that builds it.

    Notes:
        - Each run of the tree makes its own dir, in the system's temp dir.
        - The lambda runs once, at construction, and gets a ref to the path,
          not the path: it builds the body and never reads it in Python.
        - The path is a plain ``str`` in the attrs, so a body teleported to
          an ``nustd.mp`` worker with ``carry=True`` reads it there.

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
    inner, (name,) = bind("fs.tmp", body, root_key=root_key)
    if name is not None:
        inner = _Root(inner, FsRef(tags[0] if tags else ""), name)
    return Provide(FsFabric, kwargs=options, body=inner, tags=tags)


class _Root(Bracket):
    """Bind the mount's absolute path in ``ctx.attrs`` under ``name`` for the body's span."""

    def __init__(self, body: Nu | None, ref: FsRef, name: str | Nu) -> None:
        # Children: [body, where, name].
        super().__init__(body, ref.where(), name)

    @contextmanager
    def _open(  # pyright: ignore[reportIncompatibleMethodOverride] - config named
        self, ctx: Context, where: object, name: object
    ) -> Iterator[Context]:
        with ctx.attrs.let(name, where):
            yield ctx


def _tags(tag: object) -> tuple[object, ...]:
    """The binding's tags: none for ``""``, else the one tag, a term kept as given."""
    if isinstance(tag, FsRef):
        tag = tag.tag
        if isinstance(tag, Literal):
            tag = tag.value
    tag = check_tag(tag)
    return () if isinstance(tag, str) and not tag else (tag,)
