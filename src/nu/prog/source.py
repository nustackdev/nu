"""Construct a Nu term from python source.

Python source is the authoring format for a stored Nu program, and a Nu
tree is what source lowers *to*. This module is that lowering, and only
that: source text in, one Nu term out (or a :class:`Diagnostic`).

A *script*, not an expression. An expression cannot say
``class Movie(nu.Service)``, so the unit is a module with an **entry
point** -- by default a function named ``out``. The entry point's
signature is the scope contract: a snippet that needs a path marker
writes ``def out(path):`` and thereby declares it, instead of relying on
an out-of-band convention about what happens to be in scope.

    class Movie(nu.Service):
        title: str

    def out(path):
        return nu.Str(path)

Only plain data is bound into an entry point. Construction may happen in
another interpreter (see :mod:`nu.prog.brace`), where a live object from
the caller does not exist, so the contract is uniform across braces: the
snippet imports what it needs, and takes values.

``construct`` is total. Every way a snippet can fail is a
:class:`Diagnostic` return, never a raised exception, because the caller
may be a subprocess that has to ship the failure home. Failures in *our*
code still raise normally.
"""

from __future__ import annotations

import inspect
import linecache
import traceback as _tb
from typing import TYPE_CHECKING

from .diagnostics import Diagnostic


if TYPE_CHECKING:
    from collections.abc import Mapping

    from nu.lang.nu import Nu


__all__ = ["DEFAULT_ENTRY", "DEFAULT_FILENAME", "construct"]


DEFAULT_ENTRY = "out"
DEFAULT_FILENAME = "<nu program>"


def _register(source: str, filename: str) -> None:
    """Make ``source`` visible to traceback rendering under ``filename``.

    ``exec`` of a compiled code object leaves no file on disk, so frames
    from the snippet render as a bare line number with no source line.
    Seeding linecache gives the diagnostic its actual text back.
    """
    linecache.cache[filename] = (len(source), None, source.splitlines(keepends=True), filename)


def _lineno_in(exc: BaseException, filename: str) -> int | None:
    """Innermost line of ``filename`` in ``exc``'s traceback, if any."""
    lineno = None
    tb = exc.__traceback__
    while tb is not None:
        if tb.tb_frame.f_code.co_filename == filename:
            lineno = tb.tb_lineno
        tb = tb.tb_next
    return lineno


def _failed(exc: BaseException, message: str, filename: str) -> Diagnostic:
    """Flatten a live exception into a transportable Diagnostic."""
    return Diagnostic(
        message=f"{message}: {type(exc).__name__}: {exc}",
        lineno=_lineno_in(exc, filename),
        traceback="".join(_tb.format_exception(type(exc), exc, exc.__traceback__)),
    )


def construct(
    source: str,
    *,
    entry: str = DEFAULT_ENTRY,
    scope: Mapping[str, object] | None = None,
    filename: str = DEFAULT_FILENAME,
) -> Nu | Diagnostic:
    """Run ``source`` as a module and call its entry point for a Nu term.

    Args:
        source: python source for a whole module.
        entry: name of the entry point function in that module.
        scope: values offered to the entry point, bound **by parameter
            name**. Keys the entry point does not ask for are ignored; a
            parameter with no matching key and no default is an error.
        filename: name frames and diagnostics attribute the source to.

    Returns:
        The Nu term the entry point returned, or a Diagnostic describing
        the first thing that went wrong.
    """
    from nu.lang.nu import Nu as _Nu

    offered = dict(scope or {})
    _register(source, filename)

    try:
        code = compile(source, filename, "exec")
    except SyntaxError as exc:
        return Diagnostic(
            message=f"source does not parse: {exc.msg}",
            lineno=exc.lineno,
            traceback="".join(_tb.format_exception(type(exc), exc, exc.__traceback__)),
        )

    namespace: dict[str, object] = {"__name__": "__nu_program__", "__file__": filename}
    try:
        exec(code, namespace)  # noqa: S102 -- running the source is the point
    except BaseException as exc:
        return _failed(exc, "source raised while loading", filename)

    fn = namespace.get(entry)
    if fn is None:
        return Diagnostic(message=f"source defines no entry point {entry!r}")
    if not callable(fn):
        return Diagnostic(
            message=f"entry point {entry!r} is not callable, it is {type(fn).__name__}"
        )

    try:
        bound = _bind(fn, offered)
    except _UnboundError as exc:
        return Diagnostic(message=str(exc))

    try:
        term = fn(**bound)
    except BaseException as exc:
        return _failed(exc, f"entry point {entry!r} raised", filename)

    if not isinstance(term, _Nu):
        return Diagnostic(
            message=f"entry point {entry!r} returned {type(term).__name__}, expected a Nu term"
        )
    return term


class _UnboundError(Exception):
    """A parameter the entry point declared and the scope did not offer."""


def _bind(fn: object, offered: dict[str, object]) -> dict[str, object]:
    """Pick the subset of ``offered`` that ``fn``'s signature asks for.

    The signature is the contract, so surplus keys are dropped rather
    than passed. A declared parameter with no offer and no default is
    the snippet asking for something this scope cannot give.
    """
    try:
        sig = inspect.signature(fn)  # type: ignore[arg-type]
    except (TypeError, ValueError):
        # No introspectable signature (a builtin, a weird callable). Offer
        # nothing and let the call itself fail with the real error.
        return {}

    bound: dict[str, object] = {}
    missing: list[str] = []
    for name, param in sig.parameters.items():
        if param.kind in (param.VAR_POSITIONAL, param.VAR_KEYWORD):
            continue
        if name in offered:
            bound[name] = offered[name]
        elif param.default is param.empty:
            missing.append(name)
    if missing:
        available = sorted(offered) or ["nothing"]
        msg = (
            f"entry point needs {missing!r} which this scope does not offer; "
            f"available: {available!r}"
        )
        raise _UnboundError(msg)
    return bound
