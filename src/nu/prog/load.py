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

Children and fields
-------------------

``[source, entry, filename, scope, brace, rewrite]``, and no fields. Nothing
here is read before the program runs, so everything is a child, and a source
address, an entry point name, a scope, a brace tag and a rewrite are all
things a program can compute (a section path read from kv is the motivating
case). ``scope`` is one child yielding the whole mapping: a plain mapping
becomes a ``DictOf`` of its values, so each value can be a term, and a term
yielding a dict can stand in for the lot.

Failures
--------

A :class:`~nu.prog.diagnostics.Diagnostic` becomes a raised
:class:`~nu.prog.diagnostics.ConstructionError`. ``LoadNu`` yields a Nu term
or raises; it never yields a Diagnostic, because a downstream ``Eval`` would
have to re-check for one on every value that passes through it. The record
itself stays reachable on ``.diagnostic``, which is what a feedback loop
handing the failure back to its author reads.

A rewrite reaches the whole term it is handed, ``Eval`` carriers included,
because a carrier is a plain child. A term some *other* load builds at run
time is that load's own: it gets the rewrite bound on it, not this one.

Async classification: portable. The construction is blocking (a venv brace
sits on a pipe read for its whole duration), so ``_acompile`` runs it
off-thread rather than declaring the atom async-only.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, cast

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
    from nu.tree import Transform


__all__ = ["LoadNu"]


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
        entry: name of the entry point in that module: a term, or a function returning one.
        scope: plain-data values offered to the entry point, bound by
            parameter name: a mapping whose values may be computed terms, or
            one Nu yielding the whole dict. They must end up picklable for a
            venv brace.
        filename: name frames and diagnostics attribute the source to.
        brace: tag identifying the :class:`~nu.prog.brace.PyBrace` on ctx,
            or any Nu yielding one. Omit for the untagged singleton, or for
            no brace at all.
        rewrite: a ``Nu -> Nu`` transform run on the constructed term
            before it is yielded, or any Nu yielding one. The binding context for *where* the term
            lands, the way ``scope`` is the binding context for what it
            reads: :func:`nu.shape.rerooter` is the one that splices a
            snippet's bare ref chains under the block that owns them.

    Notes:
        - Every argument is a child, evaluated on each run, so all of them
          are computable: reading the source out of kv at an address the
          program itself worked out is the same node with a different
          child.
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
          neither a term nor callable, it raises, or it returns something
          that is not a Nu.
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
          is the point of it being a slot. A nested load builds its term
          later, so it rewrites with its own slot, never with this one.

    Yields:
        The Nu term the entry point returned, rewritten and unevaluated.

    Raises:
        ConstructionError: the source did not construct. The record is on
            ``.diagnostic``.

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
        scope: Mapping[str, object] | Nu | None = None,
        filename: StrArg = DEFAULT_FILENAME,
        brace: object = UNSET,
        rewrite: Transform | Nu | None = None,
    ) -> None:
        super().__init__(source, entry, filename, _scope_child(scope), brace, rewrite)

    @staticmethod
    def _brace_of(rt: Runtime, raw: object) -> PyBrace:
        """The brace bound under ``raw`` (UNSET for untagged), or the shared in-process one."""
        tag: tuple[object, ...] = () if raw is UNSET else (raw,)
        if rt.ctx.fabrics.has(PyBrace, *tag):
            return rt.ctx.fabrics.get(PyBrace, *tag)
        return _FALLBACK

    @staticmethod
    def _term(result: object, rewrite: object) -> Nu:
        """Unwrap a construct result, turning a Diagnostic into a raise, then rewrite."""
        if isinstance(result, Diagnostic):
            raise ConstructionError(result)
        if rewrite is None:
            return result  # type: ignore[return-value]
        return cast("Transform", rewrite)(cast("Nu", result))

    def _compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        source, entry, filename, scope_t, brace_t, rewrite_t = children

        def thunk(rt: Runtime) -> object:
            text, point, where = source(rt), entry(rt), filename(rt)
            scope = dict(scope_t(rt))
            built = LoadNu._brace_of(rt, brace_t(rt)).construct(
                text, entry=point, scope=scope, filename=where
            )
            return LoadNu._term(built, rewrite_t(rt))

        return thunk

    def _acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        source, entry, filename, scope_t, brace_t, rewrite_t = children

        async def athunk(rt: Runtime) -> object:
            text, point, where = await source(rt), await entry(rt), await filename(rt)
            scope = dict(await scope_t(rt))
            built = await LoadNu._brace_of(rt, await brace_t(rt)).aconstruct(
                text, entry=point, scope=scope, filename=where
            )
            return LoadNu._term(built, await rewrite_t(rt))

        return athunk


def _scope_child(scope: Mapping[str, object] | Nu | None) -> Nu:
    """The scope as its child: a term as given, a mapping as a ``DictOf`` of its values."""
    from nu.forms.collections_interactions import DictOf
    from nu.lang.nu import Nu

    if isinstance(scope, Nu):
        return scope
    return cast("Callable[..., Nu]", DictOf)(**(scope or {}))
