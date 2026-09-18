"""Braces: where python source gets constructed into a Nu tree.

A *brace* is an environment that turns source text into a Nu term. It is not
a communication channel and it does not run Nu. Exactly two things ever come
back out of one: a constructed term, or a :class:`Diagnostic`. Nothing goes
in but plain data - no live Navigator, no open connection, no session state.

Two braces, same protocol:

- :class:`InProcess` - calls :func:`nu.prog.source.construct` directly. No
  serialization, no subprocess, no cloudpickle. The default, and right for
  almost everything.
- :class:`Venv` - constructs inside a *different* interpreter, so a program
  can be authored against dependencies this process does not have.

Why constructing in a foreign interpreter works at all
------------------------------------------------------

cloudpickle pickles an importable object **by reference** and a
non-importable one **by value**, and that split is exactly the split a Nu
program needs.

A ``nu.Str(...)`` the snippet built is an instance of ``nu.core.Str``, which
the child can import, so it travels as the *name* ``nu.core.Str`` and the
parent rebinds it to its own installed ``nu``. Nothing about the child's nu
comes along.

A class the snippet mints at runtime - ``class Movie(nu.Service): ...`` -
lives in the exec namespace whose ``__name__`` is ``"__nu_program__"``, and
that module is not in ``sys.modules``. cloudpickle cannot name it, so it
serializes the class itself: bytecode, closure, annotations. The parent gets
a real working ``Movie`` that is **not** identical to any parent-side class
of the same name, and would not be even if the parent had one.

That asymmetry is the design, not a leak. The tree that comes back is
self-sufficient: shared vocabulary resolves against the parent's nu, and the
program's own inventions arrive whole.

The constraint that follows: a Venv brace's interpreter must have a
compatible ``nucore`` installed. By-reference transfer resolves names in
the parent, so the two installs have to agree on what those names mean. This
is what a Venv brace *is* - a second nu environment - and not a bug to work
around.

Whose fault is it
-----------------

A Diagnostic means *the snippet* failed: it did not parse, it raised, its
entry point is missing. Everything else - no such interpreter, the child
died mid-request, the child's ``nu`` import failed - is our failure, and
raises. A caller can retry a Diagnostic by fixing the source; it cannot fix
a dead child by editing python.
"""

from __future__ import annotations

import contextlib
import os
import struct
import subprocess
import threading
from pathlib import Path
from typing import TYPE_CHECKING, Protocol, runtime_checkable

import cloudpickle

from .diagnostics import Diagnostic
from .source import DEFAULT_ENTRY, DEFAULT_FILENAME


if TYPE_CHECKING:
    from collections.abc import Mapping
    from types import TracebackType

    from nu.lang.nu import Nu


__all__ = ["BraceError", "Constructor", "InProcess", "Venv"]


_HEADER = struct.Struct(">I")

_WORKER_MODULE = "nu.prog._construct_worker"


class BraceError(RuntimeError):
    """The brace itself failed, as opposed to the source it was given.

    Raised for a missing interpreter, a child that will not start, or a
    child that dies mid-request. A snippet's own failure is a
    :class:`Diagnostic` return and never this.
    """


@runtime_checkable
class Constructor(Protocol):
    """Anything that can turn source into one Nu term or a Diagnostic."""

    def construct(
        self,
        source: str,
        *,
        entry: str = DEFAULT_ENTRY,
        scope: Mapping[str, object] | None = None,
        filename: str = DEFAULT_FILENAME,
    ) -> Nu | Diagnostic:
        """Construct a Nu term from ``source``.

        Args:
            source: python source for a whole module.
            entry: name of the entry point function in that module.
            scope: plain values bound to the entry point by parameter name.
            filename: name frames and diagnostics attribute the source to.

        Returns:
            The Nu term the entry point returned, or a Diagnostic.
        """
        ...


class InProcess:
    """Construct here, in this interpreter.

    A direct call to :func:`nu.prog.source.construct`. No transport means no
    serialization step, so the term the snippet built is the exact object the
    caller gets, identity and all.

    The snippet still runs with this process's ``sys.modules`` and this
    process's ``nu``, which is the whole reason to reach for :class:`Venv`
    instead when a program was authored against something else.

    Notes:
        - No isolation of any kind. The snippet's module body runs here, so
          it can import, mutate globals and touch this process however it
          likes; the exec namespace is fresh, nothing else is.
        - Stateless across calls, so one instance is the same thing as one
          per node and the unbound fallback brace is safely shared.
        - Nothing to start and nothing to stop. ``close`` exists only so
          both braces close the same way.
    """

    def construct(
        self,
        source: str,
        *,
        entry: str = DEFAULT_ENTRY,
        scope: Mapping[str, object] | None = None,
        filename: str = DEFAULT_FILENAME,
    ) -> Nu | Diagnostic:
        """Construct a Nu term from ``source`` in this interpreter."""
        from .source import construct as _construct

        return _construct(source, entry=entry, scope=scope, filename=filename)

    def close(self) -> None:
        """No-op, kept so both braces close the same way."""

    def __enter__(self) -> InProcess:
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        tb: TracebackType | None,
    ) -> None:
        self.close()


class Venv:
    """Construct inside another interpreter, over a long-lived child process.

    ``python`` is either the interpreter itself
    (``/path/to/.venv/bin/python``) or a venv root (``/path/to/.venv``), in
    which case ``bin/python`` under it is used. On Windows the venv layout
    differs and only the direct interpreter path is accepted.

    The child is ``<python> -m nu.prog._construct_worker``, started once and
    reused across every ``construct`` call. Starting a fresh interpreter per
    snippet would cost more than the construction, and there is nothing to
    isolate between calls that a fresh exec namespace does not already
    isolate.

    Lifecycle is explicit: :meth:`start`, then calls, then :meth:`close`.
    ``construct`` starts the child on first use if you did not, and the
    context manager form is the ordinary way to use it::

        with Venv("/path/to/.venv") as brace:
            term = brace.construct(source)

    ``close`` is safe to call twice, and a construct that blows up still
    leaves the child either reusable or reaped - never orphaned.

    Args:
        python: interpreter path, or a venv root containing ``bin/python``.
        start_timeout: seconds to wait for the child's ready frame.
        cwd: working directory for the child. Defaults to inheriting ours.
        env: full environment for the child. Defaults to inheriting ours.

    Notes:
        - The interpreter path is resolved in ``__init__``, so a typo is an
          error where it was written rather than at the far end of a
          construct call.
        - The child needs a compatible ``nucore`` installed. cloudpickle
          sends anything importable by name, so the parent rebinds
          ``nu.core.Str`` to its own install and the two have to agree on
          what that name means. This is what a venv brace *is*, a second nu
          environment, not a limitation to route around.
        - A class the snippet mints at runtime travels by value instead,
          bytecode and closure and all, because it lives in a module that is
          not in ``sys.modules``. So the term that comes home is
          self-sufficient: shared vocabulary resolves here, the program's own
          inventions arrive whole, and the minted class is not identical to
          any parent-side class of the same name.
        - Terms are rebuilt by unpickling, so nothing about object identity
          survives the trip. That is the one behavioural difference from
          :class:`InProcess`.
        - Construct calls are serialized on a lock: one child, one request
          in flight, so concurrent callers queue.
        - ``construct`` starts the child on first use if you did not, and
          ``close`` is safe to call twice. A construct that blows up leaves
          the child either reusable or reaped, never orphaned.
        - A snippet that kills the interpreter outright cannot produce a
          diagnostic, so that comes back as a ``BraceError`` about a dead
          child rather than as the snippet's failure.
    """

    def __init__(
        self,
        python: str | os.PathLike[str],
        *,
        start_timeout: float = 30.0,
        cwd: str | os.PathLike[str] | None = None,
        env: Mapping[str, str] | None = None,
    ) -> None:
        self.python = _resolve_interpreter(python)
        self.start_timeout = start_timeout
        self.cwd = cwd
        self.env = dict(env) if env is not None else None
        self._proc: subprocess.Popen[bytes] | None = None
        self._lock = threading.Lock()

    # -- lifecycle -----------------------------------------------------------

    @property
    def started(self) -> bool:
        """Whether a child process is currently live."""
        return self._proc is not None

    def start(self) -> None:
        """Spawn the child and block until it reports ready.

        Raises:
            BraceError: the interpreter will not start, or starts and never
                sends its ready frame (typically a venv with no usable
                ``nu``, or one whose ``nu`` raises on import).
        """
        if self._proc is not None:
            return

        try:
            proc = subprocess.Popen(  # noqa: S603 -- interpreter path is the caller's own
                [str(self.python), "-m", _WORKER_MODULE],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=None,
                cwd=os.fspath(self.cwd) if self.cwd is not None else None,
                env=self.env,
            )
        except OSError as exc:
            raise BraceError(f"could not start brace interpreter {self.python}: {exc}") from exc

        self._proc = proc
        try:
            self._await_ready(proc)
        except BaseException:
            self.close()
            raise

    def _await_ready(self, proc: subprocess.Popen[bytes]) -> None:
        """Block on the handshake, with a timeout so a wedged child is visible.

        The read runs on a helper thread because a pipe read cannot be given
        a deadline. If it does not land in time the child is killed, which
        unblocks the thread on its own.
        """
        box: list[object] = []

        def _read() -> None:
            with contextlib.suppress(BaseException):
                box.append(_recv(proc.stdout))

        reader = threading.Thread(target=_read, name="nu-brace-handshake", daemon=True)
        reader.start()
        reader.join(self.start_timeout)

        if reader.is_alive():
            raise BraceError(
                f"brace interpreter {self.python} did not report ready within {self.start_timeout}s"
            )
        frame = box[0] if box else None
        if frame == ("ready",):
            return
        code = proc.poll()
        detail = f"exited with code {code}" if code is not None else f"sent {frame!r}"
        raise BraceError(
            f"brace interpreter {self.python} did not start ({detail}); "
            f"it needs a compatible `nucore` installed"
        )

    def close(self) -> None:
        """Stop the child. Idempotent, and never leaves a process behind."""
        proc, self._proc = self._proc, None
        if proc is None:
            return
        if proc.stdin is not None and proc.poll() is None:
            with contextlib.suppress(Exception):
                _send(proc.stdin, ("stop",))
        with contextlib.suppress(Exception):
            proc.wait(timeout=5)
        if proc.poll() is None:
            with contextlib.suppress(Exception):
                proc.kill()
            with contextlib.suppress(Exception):
                proc.wait(timeout=2)
        for pipe in (proc.stdin, proc.stdout):
            if pipe is not None:
                with contextlib.suppress(Exception):
                    pipe.close()

    def __enter__(self) -> Venv:
        self.start()
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        tb: TracebackType | None,
    ) -> None:
        self.close()

    def __del__(self) -> None:
        with contextlib.suppress(Exception):
            self.close()

    # -- construction --------------------------------------------------------

    def construct(
        self,
        source: str,
        *,
        entry: str = DEFAULT_ENTRY,
        scope: Mapping[str, object] | None = None,
        filename: str = DEFAULT_FILENAME,
    ) -> Nu | Diagnostic:
        """Construct ``source`` in the child and bring the result home.

        Args:
            source: python source for a whole module.
            entry: name of the entry point function in that module.
            scope: plain values bound by parameter name. They are pickled to
                the child, so they must be picklable and they must mean the
                same thing on both sides.
            filename: name frames and diagnostics attribute the source to.

        Returns:
            The Nu term, rebuilt in this process, or a Diagnostic describing
            what the snippet did wrong.

        Raises:
            BraceError: the child could not be started, died during the
                request, or answered with a frame we do not understand. None
                of these are the snippet's doing.
        """
        if self._proc is None:
            self.start()
        proc = self._proc
        assert proc is not None  # noqa: S101 -- start() either sets it or raised

        request = ("construct", source, entry, dict(scope) if scope else None, filename)
        with self._lock:
            reply = self._exchange(proc, request)

        kind = reply[0] if isinstance(reply, tuple) and reply else None
        if kind == "ok":
            return reply[1]
        if kind == "diag":
            diag = reply[1]
            if not isinstance(diag, Diagnostic):
                raise BraceError(f"brace sent a malformed diagnostic: {diag!r}")
            return diag
        raise BraceError(f"brace sent an unexpected frame: {reply!r}")

    def _exchange(self, proc: subprocess.Popen[bytes], request: tuple) -> object:
        """One request, one reply. A broken pipe means the child is gone."""
        try:
            _send(proc.stdin, request)
        except (BrokenPipeError, OSError, ValueError) as exc:
            self.close()
            raise BraceError(f"brace died before it could take the request: {exc}") from exc

        try:
            reply = _recv(proc.stdout)
        except (OSError, ValueError, EOFError) as exc:
            self.close()
            raise BraceError(f"brace died while constructing: {exc}") from exc

        if reply is None:
            code = proc.poll()
            self.close()
            raise BraceError(
                f"brace died while constructing (exit code {code}); "
                f"a snippet that kills the interpreter cannot produce a diagnostic"
            )
        return reply


# -- interpreter resolution ------------------------------------------------


def _resolve_interpreter(python: str | os.PathLike[str]) -> Path:
    """Accept an interpreter path or a venv root, return the interpreter.

    Resolved eagerly so a typo'd path is an error at construction time
    rather than at the first ``construct`` call.
    """
    path = Path(python)
    if path.is_dir():
        candidate = path / "bin" / "python"
        if not candidate.exists():
            raise BraceError(
                f"{path} looks like a venv root but has no bin/python; "
                f"pass the interpreter path directly"
            )
        return candidate
    if not path.exists():
        raise BraceError(f"no such python interpreter: {path}")
    return path


# -- wire ------------------------------------------------------------------


def _send(stream: object, frame: object) -> None:
    """Write one length-prefixed cloudpickle frame and flush it."""
    payload = cloudpickle.dumps(frame)
    stream.write(_HEADER.pack(len(payload)))  # type: ignore[attr-defined]
    stream.write(payload)  # type: ignore[attr-defined]
    stream.flush()  # type: ignore[attr-defined]


def _recv(stream: object) -> object | None:
    """Read one frame, or ``None`` when the child's stdout has closed."""
    import pickle

    header = _read_exactly(stream, _HEADER.size)
    if header is None:
        return None
    (size,) = _HEADER.unpack(header)
    body = _read_exactly(stream, size)
    if body is None:
        return None
    return pickle.loads(body)  # noqa: S301 -- peer is a child we spawned


def _read_exactly(stream: object, size: int) -> bytes | None:
    """Read exactly ``size`` bytes; ``None`` if the stream ends first."""
    chunks: list[bytes] = []
    remaining = size
    while remaining:
        chunk = stream.read(remaining)  # type: ignore[attr-defined]
        if not chunk:
            return None
        chunks.append(chunk)
        remaining -= len(chunk)
    return b"".join(chunks)
