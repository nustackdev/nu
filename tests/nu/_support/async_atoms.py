"""Nu-layer test atoms in the three async classes, for end-to-end runtime and
flow tests against ``model/04-attributes/03-eval-modes.md``.

The core ships only runs-anywhere atoms, so the doc's worked examples (sync
threads / async gather / hybrid placement) have nothing to exercise them. These
fill the gap:

- ``RunsAnywhereAction`` - ``requires_async=False, async_affinity=True`` (default)
- ``AsyncOnlyAction``    - ``requires_async=True`` (needs a loop)
- ``SyncOnlyAction``     - ``async_affinity=False`` (harmed by a loop; belongs on a thread)

Each is a childless ``ScalarAction`` (mutating, so a valid Flow body) that writes
``threading.current_thread().name`` under its name and yields the name - so a join
is observable and the *thread* it ran on is recorded. Each atom's **wrong** path
raises, so a placement bug surfaces as an error rather than a silent pass.
"""

from __future__ import annotations

import asyncio
import threading
from typing import TYPE_CHECKING

from nu.engine.structure import Declared
from nu.lang import ScalarAction


if TYPE_CHECKING:
    from collections.abc import Callable

    from nu.lang.runtime import Runtime

__all__ = ["AsyncOnlyAction", "BoomAction", "RunsAnywhereAction", "SyncOnlyAction"]


class RunsAnywhereAction(ScalarAction):
    """Runs on whichever path it is placed on; records the thread, yields its name."""

    mutates = Declared(value=frozenset({0}))

    def __init__(self, name: str) -> None:
        super().__init__()
        self.payload["name"] = name

    def compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        name = self.payload["name"]

        def thunk(rt: Runtime) -> object:
            rt.ctx.attrs[name] = threading.current_thread().name
            return name

        return thunk

    def acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        name = self.payload["name"]

        async def athunk(rt: Runtime) -> object:
            rt.ctx.attrs[name] = threading.current_thread().name
            return name

        return athunk


class AsyncOnlyAction(ScalarAction):
    """Needs a loop. Its sync thunk raises - it must never be placed off the loop."""

    requires_async = Declared(value=True)
    mutates = Declared(value=frozenset({0}))

    def __init__(self, name: str) -> None:
        super().__init__()
        self.payload["name"] = name

    def compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        def thunk(rt: Runtime) -> object:
            msg = "AsyncOnlyAction was placed on the sync path"
            raise RuntimeError(msg)

        return thunk

    def acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        name = self.payload["name"]

        async def athunk(rt: Runtime) -> object:
            await asyncio.sleep(0)  # genuinely touch the loop
            rt.ctx.attrs[name] = threading.current_thread().name
            return name

        return athunk


class BoomAction(ScalarAction):
    """Runs-anywhere body that always raises ``ValueError(name)`` on both paths.

    For exception-propagation tests: a Flow over it must surface the error.
    """

    mutates = Declared(value=frozenset({0}))

    def __init__(self, name: str) -> None:
        super().__init__()
        self.payload["name"] = name

    def compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        name = self.payload["name"]

        def thunk(rt: Runtime) -> object:
            raise ValueError(name)

        return thunk

    def acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        name = self.payload["name"]

        async def athunk(rt: Runtime) -> object:
            raise ValueError(name)

        return athunk


class SyncOnlyAction(ScalarAction):
    """Harmed by a loop. Its async thunk raises - it must be offloaded to a thread."""

    async_affinity = Declared(value=False)
    mutates = Declared(value=frozenset({0}))

    def __init__(self, name: str) -> None:
        super().__init__()
        self.payload["name"] = name

    def compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        name = self.payload["name"]

        def thunk(rt: Runtime) -> object:
            rt.ctx.attrs[name] = threading.current_thread().name
            return name

        return thunk

    def acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        async def athunk(rt: Runtime) -> object:
            msg = "SyncOnlyAction was placed on the async/loop path"
            raise RuntimeError(msg)

        return athunk
