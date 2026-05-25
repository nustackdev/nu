"""The compile driver: ``compile(term, schema) -> Program``.

Three named acts, in order:

1. **index** -- preorder walk, dense nids, structural columns
   (``index.build_index``).
2. **attribute sweeps** -- one pass per computed attribute, in schema topo
   order, direction by flavor (``attribution.sweep_attributes``). Declared
   attributes are class constants and not stored.
3. **emit** -- reverse preorder; each Term's ``compile``/``acompile``
   captures its children's thunks (``emit.emit_thunks``).

``Program.__init__`` is a dumb constructor that initializes empty columns;
the driver runs all three acts in order. The Program is fully built when
the driver returns.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from nu2.engine.compilation.attribution import sweep_attributes
from nu2.engine.compilation.emit import emit_thunks
from nu2.engine.compilation.index import build_index
from nu2.engine.compilation.program import Program


if TYPE_CHECKING:
    from nu2.engine.structure.schema import Schema
    from nu2.engine.structure.term import Term

__all__ = ["compile"]


def compile(term: Term, schema: Schema) -> Program:
    """Compile a Term against a finalized Schema: index, attribute, emit.

    Args:
        term: the root Term of the description.
        schema: a finalized :class:`Schema`. A non-finalized schema surfaces
            as :exc:`NotFinalizedError` from ``schema.topo_order()``.

    Returns:
        A Program with every computed attribute column populated and the
        thunk columns emitted. Declared attributes are not stored; they
        resolve through the schema on demand via :meth:`Program.attr`.
    """
    program = Program(term, schema)
    build_index(program, term)
    sweep_attributes(program)
    emit_thunks(program)
    return program
