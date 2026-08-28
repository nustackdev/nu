"""``LoadNu``: read python source, yield the Nu term it constructs.

The verb that makes a stored program runnable. ``LoadNu`` takes source text
and gives back a Nu term; ``Eval`` drives a term produced at runtime. Put
together, ``Eval(LoadNu(source))`` is the whole "load a stored program and
run it" move, and the two halves stay separable: a tool that only wants to
type-check or inspect a stored program loads it without evaluating it.

Where the source comes from is the tree's business. A literal is the demo
case, but the slot takes any ``Nu[str]``, so the real one - reading the
source out of kv at an address the program computed - is the same node with
a different child.

Where it is *built* is ctx's business. ``LoadNu`` resolves a
:class:`~nu.prog.brace.PyBrace` off ``rt.ctx``; with none bound it falls
back to an in-process brace, so a bare ``LoadNu`` in a plain tree works with
no ceremony. Binding one is how a subtree opts into a different interpreter,
and ``brace=`` picks among several bound braces by tag, the same single
hashable tag ``MpWorkerRef`` / ``Teleport`` take.

Children and payload
--------------------

``[source, entry, filename, *scope_values]``, with the scope *names* in
payload. Anything Nu-computable is a child, and a source address, an entry
point name and a scope value are all things a program can compute (a section
path read from kv is the motivating case). What stays in payload is the one
thing that is not a value at all: which slot carries which name. That is
structure, in the same sense ``TryCatch.errors`` is - it shapes the call,
it is not a value the call computes.

Failures
--------

A :class:`~nu.prog.diagnostics.Diagnostic` becomes a raised
:class:`~nu.prog.diagnostics.ConstructionError`. ``LoadNu`` yields a Nu term
or raises; it never yields a Diagnostic, because a downstream ``Eval`` would
have to re-check for one on every value that passes through it. The record
itself stays reachable on ``.diagnostic``, which is what a feedback loop
handing the failure back to its author reads.

Async classification: portable. The construction is blocking (a venv brace
sits on a pipe read for its whole duration), so ``_acompile`` runs it
off-thread rather than declaring the atom async-only.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from nu.lang import ScalarQuery
from nu.lang.sentinels import UNSET

from .brace import PyBrace
from .diagnostics import ConstructionError, Diagnostic
from .source import DEFAULT_ENTRY, DEFAULT_FILENAME


if TYPE_CHECKING:
    from collections.abc import Callable, Mapping

    from nu.lang import StrArg
    from nu.lang.nu import Nu
    from nu.lang.runtime import Runtime


__all__ = ["LoadNu"]


# The brace a LoadNu uses when nothing is bound. Stateless and reusable: an
# in-process brace holds no child and no cross-call state, so one shared
# instance is the same thing as one per node.
_FALLBACK = PyBrace()


class LoadNu(ScalarQuery):
    """Construct a Nu term from python source, in the brace bound on ctx.

    Args:
        source: python source for a whole module. Any ``Nu[str]``; a bare
            string auto-wraps into a Literal.
        entry: name of the entry point function in that module.
        scope: plain-data values offered to the entry point, bound by
            parameter name. Values are Nu children, so any of them may be
            computed; they must end up picklable for a venv brace.
        filename: name frames and diagnostics attribute the source to.
        brace: tag identifying the :class:`~nu.prog.brace.PyBrace` on ctx.
            Omit for the untagged singleton, or for no brace at all.

    Raises:
        ConstructionError: the source did not construct. The record is on
            ``.diagnostic``.
    """

    def __init__(
        self,
        source: StrArg,
        *,
        entry: StrArg = DEFAULT_ENTRY,
        scope: Mapping[str, object] | None = None,
        filename: StrArg = DEFAULT_FILENAME,
        brace: object = UNSET,
    ) -> None:
        names = tuple(scope) if scope else ()
        super().__init__(source, entry, filename, *(scope[n] for n in names))
        self._payload["scope_names"] = names
        self._payload["brace"] = brace

    def _brace_of(self, rt: Runtime) -> PyBrace:
        """The bound brace, or the shared in-process one."""
        raw = self._payload["brace"]
        tag: tuple[object, ...] = () if raw is UNSET else (raw,)
        if rt.ctx.has(PyBrace, *tag):
            return rt.ctx.get(PyBrace, *tag)
        return _FALLBACK

    def _term(self, result: object) -> Nu:
        """Unwrap a construct result, turning a Diagnostic into a raise."""
        if isinstance(result, Diagnostic):
            raise ConstructionError(result)
        return result  # type: ignore[return-value]

    def _compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        source, entry, filename = children[0], children[1], children[2]
        values = children[3:]
        names = self._payload["scope_names"]
        _self = self

        def thunk(rt: Runtime) -> object:
            text, point, where = source(rt), entry(rt), filename(rt)
            scope = {name: value(rt) for name, value in zip(names, values, strict=True)}
            built = _self._brace_of(rt).construct(text, entry=point, scope=scope, filename=where)
            return _self._term(built)

        return thunk

    def _acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        source, entry, filename = children[0], children[1], children[2]
        values = children[3:]
        names = self._payload["scope_names"]
        _self = self

        async def athunk(rt: Runtime) -> object:
            text, point, where = await source(rt), await entry(rt), await filename(rt)
            scope = {name: await value(rt) for name, value in zip(names, values, strict=True)}
            built = await _self._brace_of(rt).aconstruct(
                text, entry=point, scope=scope, filename=where
            )
            return _self._term(built)

        return athunk
