"""A temp dir's path, handed to a lambda, reaches an ``nustd.mp`` worker.

The mount itself stays in the caller's process. What travels is the path, a
plain string: ``fs.tmp`` hands it to its lambda through a mem frame, and the
Teleport hands it on to the worker as an arg, evaluated in the caller.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import TYPE_CHECKING, cast

import pytest

import nu
from nustd import fs
from nustd.mp import Launch, Teleport, WorkerPool


if TYPE_CHECKING:
    from collections.abc import Callable


pytestmark = pytest.mark.slow


class Local(nu.Shape):
    """The worker the tree launched."""

    w = nu.mem.IntRef.slot()


W = Local.w

isdir = cast("Callable[..., nu.Nu]", nu.host(os.path.isdir))
getpid = cast("Callable[..., nu.Nu]", nu.host(os.getpid))


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
                    Teleport(
                        None,
                        lambda root: nu.List.of(root, isdir(root), getpid()),
                        W,
                        root=root,
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


def test_a_teleport_arg_hands_the_tmp_path_to_a_worker():
    _check(nu.run(_shipped("nu-test-fs-tmp"))[0])


async def test_a_teleport_arg_hands_the_tmp_path_to_a_worker_async():
    _check((await nu.arun(_shipped("nu-test-fs-tmp-a")))[0])
