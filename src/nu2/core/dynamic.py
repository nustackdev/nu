"""Dynamic atoms: Python's runtime evaluation builtins.

Maps Python's meta-evaluation builtins onto Nu. ``eval`` / ``compile`` are
pure Queries (compute a value / a code object from operand values); ``exec``
mutates a namespace, so it leans Action; ``globals`` / ``locals`` read the live
namespace fabric.

Builtins to cover (Python -> Nu):
- ``eval`` -> ``Eval`` (Q, evaluable: evaluate an expression to a value)
- ``compile`` -> ``Compile`` (Q, evaluable: source -> code object)
- ``exec`` -> ``Exec`` (A, structural: run statements, mutate the namespace)
- ``globals`` -> ``Globals``, ``locals`` -> ``Locals`` (Q, structural)

THE RULE applied conservatively: anything that touches the live interpreter
namespace needs a fabric that is not wired yet, so it stays structural (no
``compile`` hot path). ``Eval`` / ``Compile`` stay pure - they only fold over
their operand values (the source, and optional explicit globals/locals dicts
passed as children), never reaching into a live Context. They mirror
``literal.py``: ``compile`` / ``acompile`` return a thunk over precompiled
child thunks, with EMPTY / INVALID sentinel propagation.

``Globals`` / ``Locals`` read the live namespace fabric and ``Exec`` writes it
(slot 0 = the namespace Ref), so they are declared structurally and wait for
that fabric. These touch the host interpreter; keep them thin and explicit
about which namespace Ref is read or written. Interactive-only builtins
(``breakpoint``, ``help``) are out of this pass.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from nu2.engine.structure import Declared
from nu2.lang import ScalarAction, ScalarQuery
from nu2.lang.sentinels import EMPTY, INVALID


if TYPE_CHECKING:
    from collections.abc import Callable

    from nu2.lang.runtime import Runtime

__all__ = ["Compile", "Eval", "Exec", "Globals", "Locals"]


# --- evaluable: pure value -> value over operands ------------------------


class Eval(ScalarQuery):
    """Evaluate an expression string (Python ``eval``).

    Folds over operand values only: child 0 is the expression source, optional
    children 1 / 2 are the explicit globals / locals dicts. Pure - it never
    reaches into a live Context, only the values its children yield. A sentinel
    operand (EMPTY or INVALID) collapses the result to INVALID.
    """

    def compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:  # noqa: D102
        def thunk(rt: Runtime) -> object:
            args = []
            for ct in children:
                v = ct(rt)
                if v is EMPTY or v is INVALID:
                    return INVALID
                args.append(v)
            return eval(*args)  # noqa: S307

        return thunk

    def acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:  # noqa: D102
        async def athunk(rt: Runtime) -> object:
            args = []
            for ct in children:
                v = await ct(rt)
                if v is EMPTY or v is INVALID:
                    return INVALID
                args.append(v)
            return eval(*args)  # noqa: S307

        return athunk


class Compile(ScalarQuery):
    """Compile source to a code object (Python ``compile``).

    Folds over operand values only: child 0 is the source, child 1 the
    filename, child 2 the mode (``"eval"`` / ``"exec"`` / ``"single"``). Pure -
    it produces a code object from its operands and touches no Context. A
    sentinel operand (EMPTY or INVALID) collapses the result to INVALID.
    """

    def compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:  # noqa: D102
        def thunk(rt: Runtime) -> object:
            args = []
            for ct in children:
                v = ct(rt)
                if v is EMPTY or v is INVALID:
                    return INVALID
                args.append(v)
            return compile(*args)

        return thunk

    def acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:  # noqa: D102
        async def athunk(rt: Runtime) -> object:
            args = []
            for ct in children:
                v = await ct(rt)
                if v is EMPTY or v is INVALID:
                    return INVALID
                args.append(v)
            return compile(*args)

        return athunk


# --- structural: read the live namespace fabric (NO compile) -------------


class Globals(ScalarQuery):
    """The module-level namespace dict (Python ``globals``).

    Reads the live interpreter namespace, so it is structural and waits for the
    namespace fabric - no pure ``compile`` hot path.
    """


class Locals(ScalarQuery):
    """The current local namespace dict (Python ``locals``).

    Reads the live interpreter namespace, so it is structural and waits for the
    namespace fabric - no pure ``compile`` hot path.
    """


# --- structural: mutate a namespace (NO compile) -------------------------


class Exec(ScalarAction):
    """Run statements against a namespace (Python ``exec``).

    Writes the namespace Ref in slot 0; remaining slots (source, explicit
    globals / locals) bind in read role. Mutating the live namespace needs the
    namespace fabric, so it is declared structurally with no ``compile`` hot
    path.
    """

    mutates = Declared(value=frozenset({0}))
