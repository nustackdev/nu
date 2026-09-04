"""IO: console read/write through the stdio fabric.

Maps Python's console builtins onto Nu. This file crosses sorts: a write that
yields nothing is a Command, a read that yields a value is an Action (effect +
yield in one atom).

- ``print`` -> ``Print`` (write to stdout, yields nothing -> Command)
- ``input`` -> ``Input`` (read a line, consume stdin + yield -> Action)

Both go **through a Ref** on the stdio fabric, exactly like any Context write:
slot 0 holds the ``StdioRef`` (``STDOUT`` / ``STDIN``), declared in ``mutates``,
so effect synthesis binds it WRITE. That is what makes two prints ordered (same
fabric) rather than reorderable - a plain value Query would read as pure and the
engine could fold or parallelize it, which for real IO is wrong.

The ergonomics: the ``print`` / ``input`` wrapper functions inject the singleton
Ref, so a caller never imports or passes it - ``io.print("hi")``, not
``Print(STDOUT, ...)``. ``print`` returns the ``Print`` atom
directly (a Form is a scalar-query and cannot hold a Command); ``input`` returns
a ``Str`` so the read line carries the full string interface.

Everything is one console fabric (one ``StdioRef`` class): the effect system
identifies a fabric by the concrete Ref class, so stdout and stdin share it and
the engine keeps console IO serial - the safe default. Splitting streams into
separate fabrics (to parallelize a read against a write) is not worth it for a
terminal. ``open`` / the filesystem fabric land later as their own fabric.

Tests (and any host embedding) can redirect the streams by binding a
``StdioBackend`` fabric on the Context; absent one, the atoms hit the real
``sys`` streams.

For logging use ``nu.std.logging`` -- it wraps Python's ``logging`` module 1-1
(same handlers, formatters, and configuration surface), so log records don't
share the stdio fabric.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, cast

from nu.engine.structure import Declared
from nu.lang import Command, Ref, ScalarAction
from nu.lang.sentinels import EMPTY, INVALID


if TYPE_CHECKING:
    from collections.abc import Callable
    from typing import IO

    from nu.forms.primitives import Str
    from nu.lang.runtime import Context, Runtime


__all__ = [
    "STDERR",
    "STDIN",
    "STDOUT",
    "Input",
    "Print",
    "StdioBackend",
    "StdioRef",
    "input",
    "print",
]


# --- backend (stream redirection for tests / embedding) ---------------------


class StdioBackend:
    """A Context fabric that overrides the real stdio streams.

    Args:
        stdout: stream to use in place of the real stdout. Optional.
        stderr: stream to use in place of the real stderr. Optional.
        stdin: stream to use in place of the real stdin. Optional.

    Notes:
        - Any stream left out falls back to the real ``sys`` stream.
        - This is the seam that lets a test assert on printed output or feed
          scripted input, without touching the real console.

    Example:
        >>> ctx = Context().bind(StdioBackend, StdioBackend(stdout=buf))
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


# --- the stdio fabric Ref ---------------------------------------------------


class StdioRef(Ref):
    """A Ref naming one standard stream. Fixed singletons: STDOUT / STDERR / STDIN.

    Args:
        name: the stream name (``"stdout"``, ``"stderr"`` or ``"stdin"``).

    Notes:
        - Unlike a Context ``AttrRef`` there is no address child: the stream
          name is an intrinsic constant carried in the payload.
        - The read thunk self-yields the stream handle; ``_write`` appends
          text and ``readline`` consumes one line. Both route through a
          bound ``StdioBackend`` when present, else the real ``sys`` stream.

    Yields:
        The resolved stream handle.
    """

    def __init__(self, name: str) -> None:
        super().__init__()
        self._payload = {"stream": name}

    def _resolve_stream(self, rt: Runtime) -> IO:
        return _stream_for(rt.ctx, cast("str", self._payload["stream"]))

    def _compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        def thunk(rt: Runtime) -> IO:
            return self._resolve_stream(rt)

        return thunk

    def _acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        async def athunk(rt: Runtime) -> IO:
            return self._resolve_stream(rt)

        return athunk

    def _write(self, rt: Runtime, value: str, nid: int) -> None:
        """Write ``value`` to this stream (the fabric's WRITE half)."""
        self._resolve_stream(rt).write(value)

    async def _awrite(self, rt: Runtime, value: str, nid: int) -> None:
        """Async sibling of :meth:`write` (the stream itself is sync)."""
        self._resolve_stream(rt).write(value)

    def readline(self, rt: Runtime, nid: int) -> str:
        """Consume one line from this stream, newline stripped."""
        return self._resolve_stream(rt).readline().rstrip("\n")

    def __repr__(self) -> str:
        return f"StdioRef.{cast('str', self._payload['stream']).upper()}"


STDOUT = StdioRef("stdout")
STDERR = StdioRef("stderr")
STDIN = StdioRef("stdin")


# --- atoms ------------------------------------------------------------------


class Print(Command):
    r"""Writes the values in slots 1.. to the stdout fabric Ref in slot 0.

    Args:
        ref: the stdio Ref to write through (``file`` in Python's ``print``).
        *values: the values to write, stringified and joined with ``sep``.
        sep: separator between values.
        end: text appended after the last value.
        flush: flush the stream after writing.

    Notes:
        - Python's ``print`` -- signature-identical. A Command: mutates the
          stdout fabric and yields nothing.
        - Slot 0 is the IO Ref it writes through, declared in ``mutates``;
          every other slot binds in read role.
        - ``sep`` / ``end`` / ``flush`` are captured at construction and
          ride in :attr:`_payload` as static Python values, never resolved
          as Nu terms.
        - If any value is EMPTY or INVALID, nothing is written at all: the
          check runs before the write, not per already-collected value.

    Yields:
        Nothing (VOID).

    Example:
        >>> ctx = Context().bind(StdioBackend, StdioBackend(stdout=buf))
        >>> run(Print(STDOUT, "hi"), ctx)
    """

    _mutates = Declared(value=frozenset({0}), name="mutates")

    def __init__(
        self,
        ref: StdioRef,
        *values: object,
        sep: str = " ",
        end: str = "\n",
        flush: bool = False,
    ) -> None:
        super().__init__(ref, *values)
        # sep/end/flush are static Python values, carried in payload -- unlike
        # values, they never resolve at eval time.
        self._payload = dict(self._payload)
        self._payload["sep"] = sep
        self._payload["end"] = end
        self._payload["flush"] = flush

    def _compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        ref = cast("StdioRef", self._children[0])
        value_thunks = children[1:]
        sep = str(self._payload["sep"])
        end = str(self._payload["end"])
        flush = bool(self._payload["flush"])

        def thunk(rt: Runtime) -> None:
            parts: list[str] = []
            for vt in value_thunks:
                v = vt(rt)
                if v is EMPTY or v is INVALID:
                    return
                parts.append(str(v))
            stream = ref._resolve_stream(rt)
            stream.write(sep.join(parts) + end)
            if flush:
                stream.flush()

        return thunk

    def _acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        ref = cast("StdioRef", self._children[0])
        value_thunks = children[1:]
        sep = str(self._payload["sep"])
        end = str(self._payload["end"])
        flush = bool(self._payload["flush"])

        async def athunk(rt: Runtime) -> None:
            parts: list[str] = []
            for vt in value_thunks:
                v = await vt(rt)
                if v is EMPTY or v is INVALID:
                    return
                parts.append(str(v))
            stream = ref._resolve_stream(rt)
            stream.write(sep.join(parts) + end)
            if flush:
                stream.flush()

        return athunk


class Input(ScalarAction):
    r"""Reads one line from the stdin fabric Ref in slot 0 and yields it.

    Args:
        ref: the stdio Ref to read through.

    Notes:
        - Python's ``input``, minus the prompt argument - a prompt would be
          a second, stdout write, deferred to land with the filesystem
          fabric.
        - A ScalarAction: mutates the stdin fabric (consuming input advances
          the read position) and yields a value in the same atom. Two reads
          in the same program yield different lines.

    Yields:
        The line read, newline stripped.

    Example:
        >>> inbuf = io.StringIO("a line\n")
        >>> ctx = Context().bind(StdioBackend, StdioBackend(stdin=inbuf))
        >>> run(Input(STDIN), ctx)[0]
        'a line'
    """

    _mutates = Declared(value=frozenset({0}), name="mutates")

    def _compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        ref = cast("StdioRef", self._children[0])

        def thunk(rt: Runtime) -> str:
            return ref.readline(rt, rt.program.children[nid][0])

        return thunk

    def _acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        ref = cast("StdioRef", self._children[0])

        async def athunk(rt: Runtime) -> str:
            return ref.readline(rt, rt.program.children[nid][0])

        return athunk


# --- wrappers (the user-facing surface; the Ref stays hidden) ---------------


def print(  # shadowing the builtin is intended
    *values: object,
    sep: str = " ",
    end: str = "\n",
    file: StdioRef | None = None,
    flush: bool = False,
) -> Print:
    r"""Write ``values`` to a stdio stream. Mirrors ``builtins.print``.

    Args:
        *values: the values to write.
        sep: separator between values.
        end: text appended after the last value.
        file: the stream to write to. Optional: defaults to :data:`STDOUT`.
        flush: flush the stream after writing.

    Notes:
        - Same signature as Python's ``print``, except ``file`` is a Nu
          ``StdioRef`` rather than a raw Python IO object, since the stdio
          fabric identifies streams by Ref. Pass :data:`STDERR` to write to
          stderr.
        - Injects the ``STDOUT`` Ref so a caller never imports or passes it.

    Yields:
        The ``Print`` atom itself, not a Form: a Command yields nothing, so
        there is nothing to wrap. Drive it with ``run`` / ``arun`` or
        compose it in a Flow.

    Example:
        >>> ctx = Context().bind(StdioBackend, StdioBackend(stdout=buf))
        >>> run(nu.core.io.print("hi"), ctx)
    """
    return Print(file if file is not None else STDOUT, *values, sep=sep, end=end, flush=flush)


def input() -> Str:  # shadowing the builtin is intended
    r"""Read one line from stdin (newline stripped) and yield it as a ``Str``.

    Notes:
        - Nu's ``input``, no prompt argument yet.
        - Injects the ``STDIN`` Ref so a caller never imports or passes it.
        - Returns a ``Str``, not a raw string, so the read line composes
          like any other string term.

    Yields:
        A Nu ``Str`` wrapping the line read.

    Example:
        >>> inbuf = io.StringIO("a line\n")
        >>> ctx = Context().bind(StdioBackend, StdioBackend(stdin=inbuf))
        >>> run(nu.core.io.input(), ctx)[0]
        'a line'
    """
    from nu.forms.primitives import Str

    return Str(Input(STDIN))
