"""IO: console read/write through the stdio fabric.

Maps Python's console builtins onto Nu. This file crosses sorts: a write that
yields nothing is a Command, a read that yields a value is an Action (effect +
yield in one atom).

- ``print`` -> ``PrintCommand`` (write to stdout, yields nothing -> Command)
- ``input`` -> ``InputAction`` (read a line, consume stdin + yield -> Action)

Both go **through a Ref** on the stdio fabric, exactly like any Context write:
slot 0 holds the ``StdioRef`` (``STDOUT`` / ``STDIN``), declared in ``mutates``,
so effect synthesis binds it WRITE. That is what makes two prints ordered (same
fabric) rather than reorderable - a plain value Query would read as pure and the
engine could fold or parallelize it, which for real IO is wrong.

The ergonomics: the ``print`` / ``input`` wrapper functions inject the singleton
Ref, so a caller never imports or passes it - ``io.print("hi")``, not
``PrintCommand(STDOUT, ...)``. ``print`` returns the ``PrintCommand`` atom
directly (a Form is a scalar-query and cannot hold a Command); ``input`` returns
a ``StrForm`` so the read line carries the full string interface.

Everything is one console fabric (one ``StdioRef`` class): the effect system
identifies a fabric by the concrete Ref class, so stdout and stdin share it and
the engine keeps console IO serial - the safe default. Splitting streams into
separate fabrics (to parallelize a read against a write) is not worth it for a
terminal. ``open`` / the filesystem fabric land later as their own fabric.

Tests (and any host embedding) can redirect the streams by binding a
``StdioBackend`` service on the Context; absent one, the atoms hit the real
``sys`` streams.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, cast

from nu.engine.structure import Declared
from nu.lang import Command, Ref, ScalarAction
from nu.lang.sentinels import EMPTY, INVALID


if TYPE_CHECKING:
    from collections.abc import Callable
    from typing import IO

    from nu.forms.primitives import StrForm
    from nu.lang.runtime import Context, Runtime


__all__ = [
    "STDERR",
    "STDIN",
    "STDOUT",
    "InputAction",
    "LogCommand",
    "PrintCommand",
    "StdioBackend",
    "StdioRef",
    "input",
    "log",
    "print",
]


# --- backend (stream redirection for tests / embedding) ---------------------


class StdioBackend:
    """A Context service that overrides the real stdio streams.

    Bind one on the Context (``ctx.bind(StdioBackend, StdioBackend(stdout=buf))``)
    to capture or redirect a stream; any stream left ``None`` falls back to the
    real ``sys`` stream. This is the seam that lets a test assert on printed
    output or feed scripted input.
    """

    def __init__(
        self,
        *,
        stdout: IO | None = None,
        stderr: IO | None = None,
        stdin: IO | None = None,
    ) -> None:
        self._streams: dict[str, IO | None] = {
            "stdout": stdout,
            "stderr": stderr,
            "stdin": stdin,
        }

    def stream_for(self, name: str) -> IO:
        """The bound stream for ``name``, or the real ``sys`` stream if unbound."""
        import sys

        stream = self._streams.get(name)
        return stream if stream is not None else getattr(sys, name)


def _stream_for(ctx: Context, name: str) -> IO:
    """Resolve a stream by name off the Context: the bound backend, else ``sys``."""
    import sys

    if ctx.has(StdioBackend):
        return ctx.get(StdioBackend).stream_for(name)
    return getattr(sys, name)


def _format_log(level: str, logger: str, parts: list[str]) -> str:
    """The one log-line shape shared by ``LogCommand`` and the annotate spans."""
    return f"[{level.upper()}] {logger}: {' '.join(parts)}\n"


def _emit_log(ctx: Context, level: str, logger: str, message: str) -> None:
    """Write one formatted log line to the stderr stream (backend-aware).

    The imperative seam for code that logs outside the atom path - notably the
    step-tracking Bracket in ``nu.inspect``, whose ``scope`` logs around a body
    and so cannot delegate to a ``LogCommand`` child.
    """
    _stream_for(ctx, "stderr").write(_format_log(level, logger, [message]))


# --- the stdio fabric Ref ---------------------------------------------------


class StdioRef(Ref):
    """A Ref naming one standard stream. Fixed singletons: STDOUT / STDERR / STDIN.

    Unlike a Context ``AttrRef`` there is no address child - the stream name is an
    intrinsic constant carried in the payload. The read thunk self-yields the
    stream handle; ``write`` appends text and ``readline`` consumes one line. Both
    route through a bound ``StdioBackend`` when present, else the real ``sys``
    stream.
    """

    def __init__(self, name: str) -> None:
        super().__init__()
        self.payload = {"stream": name}

    def _resolve_stream(self, rt: Runtime) -> IO:
        return _stream_for(rt.ctx, cast("str", self.payload["stream"]))

    def compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:  # noqa: D102
        def thunk(rt: Runtime) -> IO:
            return self._resolve_stream(rt)

        return thunk

    def acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:  # noqa: D102
        async def athunk(rt: Runtime) -> IO:
            return self._resolve_stream(rt)

        return athunk

    def write(self, rt: Runtime, value: str, nid: int) -> None:
        """Write ``value`` to this stream (the fabric's WRITE half)."""
        self._resolve_stream(rt).write(value)

    async def awrite(self, rt: Runtime, value: str, nid: int) -> None:
        """Async sibling of :meth:`write` (the stream itself is sync)."""
        self._resolve_stream(rt).write(value)

    def readline(self, rt: Runtime, nid: int) -> str:
        """Consume one line from this stream, newline stripped."""
        return self._resolve_stream(rt).readline().rstrip("\n")

    def __repr__(self) -> str:
        return f"StdioRef.{cast('str', self.payload['stream']).upper()}"


STDOUT = StdioRef("stdout")
STDERR = StdioRef("stderr")
STDIN = StdioRef("stdin")


# --- atoms ------------------------------------------------------------------


class PrintCommand(Command):
    """Writes the values in slots 1.. to the stdout fabric Ref in slot 0.

    Python's ``print``. A Command: it mutates the stdout fabric and yields
    nothing. Slot 0 is the IO Ref it writes through; every other slot binds in
    read role. Values are stringified and joined with a space, with a trailing
    newline - Python's default ``print`` shape.
    """

    mutates = Declared(value=frozenset({0}))

    def compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:  # noqa: D102
        ref = cast("StdioRef", self.children[0])
        value_thunks = children[1:]

        def thunk(rt: Runtime) -> None:
            parts: list[str] = []
            for vt in value_thunks:
                v = vt(rt)
                if v is EMPTY or v is INVALID:
                    return
                parts.append(str(v))
            ref.write(rt, " ".join(parts) + "\n", rt.program.children[nid][0])

        return thunk

    def acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:  # noqa: D102
        ref = cast("StdioRef", self.children[0])
        value_thunks = children[1:]

        async def athunk(rt: Runtime) -> None:
            parts: list[str] = []
            for vt in value_thunks:
                v = await vt(rt)
                if v is EMPTY or v is INVALID:
                    return
                parts.append(str(v))
            await ref.awrite(rt, " ".join(parts) + "\n", rt.program.children[nid][0])

        return athunk


class LogCommand(Command):
    r"""Writes a leveled, named log line to the stderr fabric Ref in slot 0.

    Children: ``[STDERR, level, logger, *values]``. Formats
    ``"[LEVEL] logger: v1 v2 ...\n"`` and writes it through the stderr Ref
    (slot 0), so it is a Command exactly like :class:`PrintCommand` - the effect
    is a fabric WRITE, testable through a bound ``StdioBackend``. What sets it
    apart from ``print`` is the ``level`` and ``logger`` name, both carried as
    ``StrArg`` children (slots 1-2) so a tree rewrite can retarget them - that is
    how ``nu.inspect.set_logger_name`` renames a logger across a whole tree. A
    value slot reading a sentinel (an unbound attr) is skipped, not fatal, so a
    log line still emits when one of its interpolated attrs is absent.
    """

    mutates = Declared(value=frozenset({0}))

    def compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:  # noqa: D102
        ref = cast("StdioRef", self.children[0])
        level_thunk, logger_thunk = children[1], children[2]
        value_thunks = children[3:]

        def thunk(rt: Runtime) -> None:
            parts: list[str] = []
            for vt in value_thunks:
                v = vt(rt)
                if v is EMPTY or v is INVALID:
                    continue
                parts.append(str(v))
            line = _format_log(str(level_thunk(rt)), str(logger_thunk(rt)), parts)
            ref.write(rt, line, rt.program.children[nid][0])

        return thunk

    def acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:  # noqa: D102
        ref = cast("StdioRef", self.children[0])
        level_thunk, logger_thunk = children[1], children[2]
        value_thunks = children[3:]

        async def athunk(rt: Runtime) -> None:
            parts: list[str] = []
            for vt in value_thunks:
                v = await vt(rt)
                if v is EMPTY or v is INVALID:
                    continue
                parts.append(str(v))
            line = _format_log(str(await level_thunk(rt)), str(await logger_thunk(rt)), parts)
            await ref.awrite(rt, line, rt.program.children[nid][0])

        return athunk


class InputAction(ScalarAction):
    """Reads one line from the stdin fabric Ref in slot 0 and yields it.

    Python's ``input`` (no prompt - that would be a second, stdout write; deferred
    with the filesystem fabric). A ScalarAction: it mutates the stdin fabric
    (consuming input advances the read position) and yields the line, newline
    stripped. Non-deterministic - two reads yield different lines - though as an
    effectful Action it is never a fold candidate anyway.
    """

    mutates = Declared(value=frozenset({0}))
    deterministic = Declared(value=False)

    def compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:  # noqa: D102
        ref = cast("StdioRef", self.children[0])

        def thunk(rt: Runtime) -> str:
            return ref.readline(rt, rt.program.children[nid][0])

        return thunk

    def acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:  # noqa: D102
        ref = cast("StdioRef", self.children[0])

        async def athunk(rt: Runtime) -> str:
            return ref.readline(rt, rt.program.children[nid][0])

        return athunk


# --- wrappers (the user-facing surface; the Ref stays hidden) ---------------


def print(*values: object) -> PrintCommand:  # shadowing the builtin is intended
    """Write ``values`` to stdout, space-separated with a trailing newline.

    Nu's ``print``: mirrors the builtin's default shape. Returns the
    ``PrintCommand`` atom (a Command yields nothing, so it is not Form-wrapped);
    drive it with ``run`` / ``arun`` or compose it in a Flow.
    """
    return PrintCommand(STDOUT, *values)


def log(*values: object, level: str = "info", logger: str = "nu") -> LogCommand:
    """Write a leveled log line to stderr: ``[LEVEL] logger: values...``.

    Nu's logging effect: like ``print`` but to stderr and tagged with a ``level``
    and ``logger`` name (both plain strings, auto-wrapped as literals). Returns
    the ``LogCommand`` atom (a Command yields nothing); drive it with ``run`` /
    ``arun`` or compose it - e.g. as a ``Retry`` failure hook.
    """
    return LogCommand(STDERR, level, logger, *values)


def input() -> StrForm:  # shadowing the builtin is intended
    """Read one line from stdin (newline stripped) and yield it as a ``StrForm``.

    Nu's ``input`` (no prompt argument yet). The ``StrForm`` carries the full
    string interface, so the read line composes like any other string term.
    """
    from nu.forms.primitives import StrForm

    return StrForm(InputAction(STDIN))
