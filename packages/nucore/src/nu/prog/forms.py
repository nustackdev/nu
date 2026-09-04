"""``Program`` - source text that constructs a Nu term, as a Form.

``Eval(LoadNu(source))`` already says "load a stored program and run it".
``Program`` is the ergonomic surface over that pair: it is a ``Nu[str]``
carrying the source, and its verbs hand back the composed tree.

Two ways in, one type. Standalone, a literal is the child::

    Program(SOURCE).run()

Stored, the child is the ref that reads the source out of a fabric. That is
what :class:`~nu.kv.refs.prog.ProgramRef` and its mem twin are - the same
Form mixed into a substrate ref, so ``Shape.program.run()`` reads the source
from storage and runs what it constructs.

Verbs compose, they do not add atoms
------------------------------------

``.load()`` and ``.run()`` are plain methods that return composed Nu. There
is no ``LoadProgram`` atom, no ``RunProgram`` atom. This is the established
idiom - ``IntRef.inc`` is literally ``return self.set(self + step)`` - and it
earns its keep twice over here. A program is a thing you store and inspect,
so the tree a verb produces should show its real control flow: a
``.run(on_error=...)`` is visibly a ``TryCatch`` around an ``Eval`` around a
``LoadNu``, walkable and attributable like any other tree. An opaque atom
would hide all three, and every consumer that reasons over trees (attribute
sweeps, effect classification, promise checks) would have to learn about it
separately.

The cost is that the verbs are not overridable per substrate. Nothing wants
that: where the source comes from is the child's business, and the child is
what differs between substrates.

Construction takes no ``.of()``. The ``nu.std`` Forms use classmethods
because their payloads need parsing atoms to build; ``Program`` does not.
``TypedNu.__init__`` wraps a single child and ``Nu`` auto-wraps a non-Term
child into a ``Literal``, so ``Program(SOURCE)`` with a bare ``str`` is
already the right node.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from nu.lang import Form, TypedNu
from nu.lang.sentinels import UNSET

from .source import DEFAULT_ENTRY, DEFAULT_FILENAME


if TYPE_CHECKING:
    from collections.abc import Mapping

    from nu.lang import Nu, StrArg


__all__ = ["Program"]


class Program(Form, TypedNu[str]):
    """Python source that constructs a Nu term.

    The child yields the source text: a literal when the program is written
    inline, a ref when it is stored. Both verbs thread the same construction
    arguments through to :class:`~nu.prog.load.LoadNu`.

    Notes:
        - The verbs compose rather than adding atoms. ``.load()`` is a
          ``LoadNu``, ``.run()`` is an ``Eval`` over it, and
          ``.run(on_error=...)`` is those two inside a ``TryCatch``. The tree
          shows the real control flow, so attribute sweeps, effect
          classification and promise checks all reach it with no special
          case for programs.
        - Mixed into a substrate ref it becomes a program-valued slot
          (``nu.kv``'s ``ProgramRef`` and its ``nu.mem`` twin), where the
          child is what reads the source out of storage. Nothing else about
          the Form changes, which is why the verbs are not overridable per
          substrate.
        - No ``.of()`` constructor. ``Program(source)`` with a bare ``str``
          is already the right node, because ``Nu`` auto-wraps a non-Term
          child into a ``Literal``.
        - Everything the value carries is a ``Str``: source text is what a
          program is until something constructs it.

    Example:
        >>> src = '''
        ... import nu
        ... def out():
        ...     return nu.Int(6) * nu.Int(7)
        ... '''
        >>> nu.run(nu.prog.Program(src).run())[0]
        42
    """

    def load(
        self,
        *,
        entry: StrArg = DEFAULT_ENTRY,
        scope: Mapping[str, object] | None = None,
        filename: StrArg = DEFAULT_FILENAME,
        brace: object = UNSET,
    ) -> Nu:
        """Construct the term without running it.

        The half a type-checker or an inspector wants: the source becomes a
        Nu term and stops there.

        Args:
            entry: name of the entry point function in the source module.
            scope: plain-data values offered to the entry point, bound by
                parameter name.
            filename: name frames and diagnostics attribute the source to.
            brace: tag identifying the :class:`~nu.prog.brace.PyBrace` on
                ctx. Omit for the untagged singleton, or for no brace.

        Notes:
            - Constructing runs the module body and calls the entry point,
              so a snippet with import-time side effects has them here even
              though nothing evaluates the term afterwards.

        Returns:
            A ``LoadNu`` over this source.

        Raises:
            ConstructionError: at runtime, when the source did not
                construct. The record is on ``.diagnostic``.
        """
        from .load import LoadNu

        return LoadNu(self, entry=entry, scope=scope, filename=filename, brace=brace)

    def run(
        self,
        *,
        entry: StrArg = DEFAULT_ENTRY,
        scope: Mapping[str, object] | None = None,
        filename: StrArg = DEFAULT_FILENAME,
        brace: object = UNSET,
        on_error: Nu | None = None,
    ) -> Nu:
        """Construct the term and drive it.

        Args:
            entry: name of the entry point function in the source module.
            scope: plain-data values offered to the entry point, bound by
                parameter name.
            filename: name frames and diagnostics attribute the source to.
            brace: tag identifying the :class:`~nu.prog.brace.PyBrace` on
                ctx.
            on_error: branch to run when construction fails. Given one, the
                whole thing is wrapped in a ``TryCatch`` filtered to
                ``ConstructionError``, and the branch reads the caught
                exception off the attrs fabric with ``AttrRef("error")``.
                Only construction failures are caught; whatever the program
                itself raises propagates.

        Notes:
            - The result is one ``Eval``, so the program runs exactly once
              however many places read the yield. Compose the same
              ``.run()`` into two slots and it constructs and runs twice,
              which for a program that appends to a list is a silently
              wrong world; store the yield in a Ref and read that instead.
            - ``on_error`` catches construction only. A program that
              constructs and then raises while running propagates, so wrap
              the whole thing in a second ``TryCatch`` when that failure
              should also be an outcome rather than a crash.

        Returns:
            An ``Eval`` over the loaded term, wrapped in a ``TryCatch`` when
            ``on_error`` is given.
        """
        from nu.core.spans import TryCatch

        from .diagnostics import ConstructionError
        from .eval import Eval

        running = Eval(self.load(entry=entry, scope=scope, filename=filename, brace=brace))
        if on_error is None:
            return running
        return TryCatch(running, catch=on_error, errors=ConstructionError)
