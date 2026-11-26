"""A temp dir's path, handed to a lambda, reaches an ``nustd.mp`` worker.

The mount itself stays in the caller's process. What travels is the path, a
plain string. ``fs.tmp`` hands it to its lambda through a mem frame, which no
teleport carries, so until Teleport takes its values as arguments (task-184
phase 4) this test parks the path in ``ctx.attrs`` itself, which
``Teleport(..., carry=True)`` copies to the worker.
"""

from __future__ import annotations

import os
from contextlib import contextmanager
from pathlib import Path
from typing import TYPE_CHECKING, cast

import pytest

import nu
from nustd import fs
from nustd.mp import Launch, Teleport, WorkerPool


if TYPE_CHECKING:
    from collections.abc import Callable, Iterator

    from nu.lang.runtime import Context


pytestmark = pytest.mark.slow


class Local(nu.Shape):
    """The worker the tree launched."""

    w = nu.mem.IntRef.slot()


W = Local.w

isdir = cast("Callable[..., nu.Nu]", nu.host(os.path.isdir))
getpid = cast("Callable[..., nu.Nu]", nu.host(os.getpid))


class _Park(nu.Bracket):
    """TEMPORARY (task-184 phase 4): park ``value`` in attrs under ``"root"`` for the body."""

    def __init__(self, body: nu.Nu, value: object) -> None:
        super().__init__(body, value)

    @contextmanager
    def _open(self, ctx: Context, value: object) -> Iterator[Context]:  # type: ignore[override]
        with ctx.attrs.let("root", value):
            yield ctx


ROOT = nu.Attr("root")


def _shipped(name: str) -> nu.Nu:
    """A tmp whose body asks a worker for the path, whether it is a dir there, and its pid."""
    return fs.tmp(
        prefix="fs-worker-",
        body=lambda root: nu.Provide(
            WorkerPool,
            kwargs={"name": name},
            body=nu.mem.let(
                Local,
                nu.List.of(
                    root,
                    _Park(
                        Teleport(
                            body=nu.List.of(ROOT, isdir(ROOT), getpid()), worker=W, carry=True
                        ),
                        root,
                    ),
                ),
                w=Launch(),
            ),
        ),
    )


def _check(got: list) -> None:
    here, (there, is_dir, pid) = got
    assert there == here
    assert is_dir is True
    assert pid != os.getpid()
    assert not Path(here).exists()


def test_a_carried_teleport_reads_the_tmp_path():
    _check(nu.run(_shipped("nu-test-fs-tmp"))[0])


async def test_a_carried_teleport_reads_the_tmp_path_async():
    _check((await nu.arun(_shipped("nu-test-fs-tmp-a")))[0])
