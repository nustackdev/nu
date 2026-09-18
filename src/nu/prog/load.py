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

Where the term *lands* is the loader's business. ``rewrite`` is a
``Nu -> Nu`` transform applied to the constructed term before anyone can see
it, which is where re-rooting a snippet's bare ref chains under the block that
owns them goes (:func:`nu.shape.rerooter`). It sits on ``LoadNu`` rather than
being a node someone composes in front of ``Eval`` for one reason: on the slot
there is no way to obtain a term that skipped it, and composed in front there
is, and forgetting it writes to the wrong paths silently.

Where it is *built* is ctx's business. ``LoadNu`` resolves a
:class:`~nu.prog.brace.PyBrace` off ``rt.ctx``; with none bound it falls
back to an in-process brace, so a bare ``LoadNu`` in a plain tree works with
no ceremony. Binding one is how a subtree opts into a different interpreter,
and ``brace=`` picks among several bound braces by tag, the same single
hashable tag ``Teleport`` takes.

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

A rewrite reaches the whole term it is handed, ``Eval`` carriers included,
because a carrier is a plain child. The one thing it cannot reach is a term
some *other* load builds at run time, inside a nested Runtime, after this
rewrite already ran. Rather than let that term through un-rewritten and write
to bare paths, a load carrying a rewrite refuses to yield a term with another
``LoadNu`` in it (:class:`RewriteEscapeError`). Nothing nests loads today.

Async classification: portable. The construction is blocking (a venv brace
sits on a pipe read for its whole duration), so ``_acompile`` runs it
off-thread rather than declaring the atom async-only.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from nu.lang import ScalarQuery
from nu.lang.sentinels import UNSET
from nu.tree.walk import preorder

from .brace import PyBrace
from .diagnostics import ConstructionError, Diagnostic
from .source import DEFAULT_ENTRY, DEFAULT_FILENAME


if TYPE_CHECKING:
    from collections.abc import Callable, Mapping

    from nu.lang import StrArg
    from nu.lang.nu import Nu
    from nu.lang.runtime import Runtime
    from nu.tree import Transform


__all__ = ["LoadNu", "RewriteEscapeError"]


class RewriteEscapeError(RuntimeError):
    """A load's rewrite cannot reach a term another load builds at run time.

    Raised when a ``LoadNu`` carrying a ``rewrite`` constructs a term that
    holds another ``LoadNu``. The inner load runs later, in its own Runtime,
    so whatever it builds is never handed to this rewrite. Bind the rewrite
    on the inner load instead of nesting one inside the other.
    """


# The brace a LoadNu uses when nothing is bound. Stateless and reusable: an
# in-process brace holds no child and no cross-call state, so one shared
# instance is the same thing as one per node.
_FALLBACK = PyBrace()


class LoadNu(ScalarQuery):
    """Constructs a Nu term from python source, in the brace bound on ctx.

    The source is a whole module, not an expression, and the term comes from
    calling its entry point. The entry point's own signature is the scope
    contract: it declares by name what it needs, ``scope`` offers values by
    name, and only the intersection is passed. So a snippet says what it
    depends on rather than trusting an out-of-band convention about what
    happens to be in scope.

    Constructing is not running. ``LoadNu`` gives back the term and stops
    there, which is what a tool that wants to inspect or type-check a stored
    program needs; ``Eval(LoadNu(source))`` is the pair that also drives it.

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
        rewrite: a ``Nu -> Nu`` transform run on the constructed term
            before it is yielded. The binding context for *where* the term
            lands, the way ``scope`` is the binding context for what it
            reads: :func:`nu.shape.rerooter` is the one that splices a
            snippet's bare ref chains under the block that owns them.

    Notes:
        - Source, entry, filename and every scope value are children, so all
          four are computable: reading the source out of kv at an address
          the program itself worked out is the same node with a different
          child. Only the mapping from slot to scope name lives in payload,
          because it shapes the call rather than being a value the call
          computes.
        - The brace is resolved off ``rt.ctx`` at evaluation, by
          ``PyBrace`` plus the ``brace`` tag. With nothing bound it falls
          back to a shared in-process brace, so a bare ``LoadNu`` in a plain
          tree needs no bracket.
        - Only plain data crosses into a brace. A venv brace pickles the
          scope to another interpreter, where a live object from this one
          does not exist, so the snippet imports what it needs and takes
          values.
        - Scope keys the entry point does not declare are dropped rather
          than passed. A declared parameter with no offer and no default is
          a construction failure, not a ``TypeError``.
        - Every way the snippet can fail is one failure: the source does not
          parse, module-level code raises, the entry point is missing or is
          not callable, it raises, or it returns something that is not a Nu.
          All five come back as a ``Diagnostic`` and are raised as one
          ``ConstructionError``.
        - It never yields a Diagnostic, only raises. A downstream ``Eval``
          would otherwise have to re-check every value passing through it
          for one.
        - The traceback in a diagnostic renders the snippet's actual source
          lines, because the source is seeded into ``linecache`` under
          ``filename`` before it is compiled.
        - Portable across sync and async. Construction is blocking (a venv
          brace sits on a pipe read for its whole duration), so the async
          path runs it off-thread rather than making the atom async-only.
        - The rewrite runs on this side of the brace, on the term that came
          back, so it is a live python callable and never has to pickle.
        - A rewrite is bound per load and there is no way around it, which
          is the point of it being a slot. A load with a rewrite refuses to
          yield a term holding another ``LoadNu``, because that inner load
          builds its term later and would escape.

    Yields:
        The Nu term the entry point returned, rewritten and unevaluated.

    Raises:
        ConstructionError: the source did not construct. The record is on
            ``.diagnostic``.
        RewriteEscapeError: a rewrite is bound and the term holds a nested
            ``LoadNu``, whose own term the rewrite could never reach.

    Example:
        >>> src = '''
        ... import nu
        ... def out(n):
        ...     return nu.Int(n) * nu.Int(10)
        ... '''
        >>> nu.run(nu.LoadNu(src, scope={"n": 4}))[0]
        Int(Mul(Int(4), Int(10)))

        >>> try:
        ...     nu.run(nu.LoadNu("def out( "))
        ... except nu.prog.ConstructionError as err:
        ...     print(err.diagnostic)
        source does not parse: '(' was never closed (line 1)
    """

    def __init__(
        self,
        source: StrArg,
        *,
        entry: StrArg = DEFAULT_ENTRY,
        scope: Mapping[str, object] | None = None,
        filename: StrArg = DEFAULT_FILENAME,
        brace: object = UNSET,
        rewrite: Transform | None = None,
    ) -> None:
        names = tuple(scope) if scope else ()
        super().__init__(source, entry, filename, *(scope[n] for n in names))
        self._payload["scope_names"] = names
        self._payload["brace"] = brace
        self._payload["rewrite"] = rewrite

    def _brace_of(self, rt: Runtime) -> PyBrace:
        """The bound brace, or the shared in-process one."""
        raw = self._payload["brace"]
        tag: tuple[object, ...] = () if raw is UNSET else (raw,)
        if rt.ctx.has(PyBrace, *tag):
            return rt.ctx.get(PyBrace, *tag)
        return _FALLBACK

    def _term(self, result: object) -> Nu:
        """Unwrap a construct result, turning a Diagnostic into a raise, then rewrite."""
        if isinstance(result, Diagnostic):
            raise ConstructionError(result)
        rewrite: Transform | None = self._payload["rewrite"]  # type: ignore[assignment]
        if rewrite is None:
            return result  # type: ignore[return-value]
        return self._reachable(rewrite(result))  # type: ignore[arg-type]

    def _reachable(self, term: Nu) -> Nu:
        """Refuse a rewritten term holding a load whose own term would escape."""
        for node in preorder(term):
            if isinstance(node, LoadNu):
                msg = (
                    "LoadNu: a rewrite is bound here, but the constructed term "
                    "holds another LoadNu. That load builds its term at run "
                    "time, in its own Runtime, so this rewrite never sees it "
                    "and it would resolve against bare paths. Bind the rewrite "
                    "on the inner load instead."
                )
                raise RewriteEscapeError(msg)
        return term

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
