"""I/O ops -- Print, Log, Debug.

Commands that write to stdio. All declare own_effects = {0: WRITE}
on the StdioRef position.
"""

from __future__ import annotations

import logging
from typing import Any, ClassVar

from nu.stdio.refs import STDERR, STDOUT
from nu.terms.command import ScalarCommand
from nu.terms.types import Effect, Mode


__all__ = [
    "Debug",
    "Log",
    "Noop",
    "Print",
]


_BOTH = frozenset({Mode.SYNC, Mode.ASYNC})


class Noop(ScalarCommand):
    """No-op command. Does nothing. No effects, no children.

    Useful as a placeholder/identity in compositions (e.g. an `IfDo`
    else-branch, a default tree, a sentinel that satisfies a Nu argument
    without producing observable behavior).
    """

    support: ClassVar[frozenset[Mode]] = _BOTH

    def __init__(self) -> None:
        super().__init__()

    def run(self, ctx: Any) -> None:  # noqa: ANN401
        return

    async def arun(self, ctx: Any) -> None:  # noqa: ANN401
        return

    def __repr__(self) -> str:
        return "Noop()"


class Print(ScalarCommand):
    """Print messages to stdout.

    Children: [StdioRef.STDOUT, message, *values]
    """

    own_effects: ClassVar[dict[int, Effect]] = {0: Effect.WRITE}
    support: ClassVar[frozenset[Mode]] = _BOTH

    def __init__(self, *values: Any) -> None:  # noqa: ANN401
        super().__init__(STDOUT, *values)

    def run(self, ctx: Any) -> None:  # noqa: ANN401
        from nu import runtime
        from nu.stdio.ops import _get_stream

        stream = _get_stream(ctx, self._children[0])
        parts = [str(runtime.collect(c, ctx)) for c in self._children[1:]]
        stream.write(" ".join(parts) + "\n")

    async def arun(self, ctx: Any) -> None:  # noqa: ANN401
        from nu import runtime
        from nu.stdio.ops import _get_stream

        stream = _get_stream(ctx, self._children[0])
        parts = [str(await runtime.acollect(c, ctx)) for c in self._children[1:]]
        stream.write(" ".join(parts) + "\n")


class Log(ScalarCommand):
    """Structured logging with configurable level.

    Children: [StdioRef.STDERR, level, logger_name, message, *values]
    """

    own_effects: ClassVar[dict[int, Effect]] = {0: Effect.WRITE}
    support: ClassVar[frozenset[Mode]] = _BOTH

    def __init__(
        self,
        message: Any,  # noqa: ANN401
        *values: Any,  # noqa: ANN401
        level: Any = "info",  # noqa: ANN401
        logger_name: Any = "nu",  # noqa: ANN401
    ) -> None:
        super().__init__(STDERR, level, logger_name, message, *values)
        self._path = ""

    def run(self, ctx: Any) -> None:  # noqa: ANN401
        from nu import runtime

        level = runtime.first(self._children[1], ctx)
        logger_name = runtime.first(self._children[2], ctx)
        parts = [str(runtime.collect(c, ctx)) for c in self._children[3:]]
        message = " ".join(parts)
        if self._path:
            message = f"[{self._path}] {message}"
        getattr(logging.getLogger(logger_name), level)(message)

    async def arun(self, ctx: Any) -> None:  # noqa: ANN401
        from nu import runtime

        level = await runtime.afirst(self._children[1], ctx)
        logger_name = await runtime.afirst(self._children[2], ctx)
        parts = [str(await runtime.acollect(c, ctx)) for c in self._children[3:]]
        message = " ".join(parts)
        if self._path:
            message = f"[{self._path}] {message}"
        getattr(logging.getLogger(logger_name), level)(message)


class Debug(ScalarCommand):
    """Quick debug output for development.

    Children: [StdioRef.STDOUT, prefix, labels, *values]
    """

    own_effects: ClassVar[dict[int, Effect]] = {0: Effect.WRITE}
    support: ClassVar[frozenset[Mode]] = _BOTH

    def __init__(
        self,
        *values: Any,  # noqa: ANN401
        labels: Any = None,  # noqa: ANN401
        prefix: Any = "[DEBUG]",  # noqa: ANN401
    ) -> None:
        super().__init__(STDOUT, prefix, labels, *values)

    def run(self, ctx: Any) -> None:  # noqa: ANN401
        from nu import runtime
        from nu.stdio.ops import _get_stream

        stream = _get_stream(ctx, self._children[0])
        prefix = runtime.first(self._children[1], ctx)
        labels = runtime.first(self._children[2], ctx)
        parts = [str(prefix)]
        for i, child in enumerate(self._children[3:]):
            val = runtime.collect(child, ctx)
            if labels and i < len(labels):
                parts.append(f"{labels[i]}={val!r}")
            else:
                parts.append(repr(val))
        stream.write(" ".join(parts) + "\n")

    async def arun(self, ctx: Any) -> None:  # noqa: ANN401
        from nu import runtime
        from nu.stdio.ops import _get_stream

        stream = _get_stream(ctx, self._children[0])
        prefix = await runtime.afirst(self._children[1], ctx)
        labels = await runtime.afirst(self._children[2], ctx)
        parts = [str(prefix)]
        for i, child in enumerate(self._children[3:]):
            val = await runtime.acollect(child, ctx)
            if labels and i < len(labels):
                parts.append(f"{labels[i]}={val!r}")
            else:
                parts.append(repr(val))
        stream.write(" ".join(parts) + "\n")
