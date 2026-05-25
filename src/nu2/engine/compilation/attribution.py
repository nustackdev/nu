"""Act 2: sweep computed attributes into the Program in topological order.

For each computed attribute, in ``schema.topo_order()``, allocate a column
on the Program and fill it by the flavor's structural direction:
synthesized leaves-up (reverse preorder), inherited root-down (preorder).
Declared attributes are class constants and are never stored
(``03-attribute.md``, ``06-store.md``); they do not appear in the order.
"""

from __future__ import annotations

from typing import TYPE_CHECKING


if TYPE_CHECKING:
    from nu2.engine.structure import Inherited, Synthesized

    from .program import Program

__all__ = ["sweep_attributes"]


def sweep_attributes(program: Program) -> None:
    """Run one sweep per computed attribute, in the schema's topological order."""
    from nu2.engine.structure import Inherited, Synthesized

    schema = program._schema
    n = len(program.terms)
    for name in schema.topo_order():
        spec = schema[name]
        column: list[object] = [None] * n
        program.attrs[name] = column
        if isinstance(spec, Synthesized):
            _synthesize(program, spec, column)
        elif isinstance(spec, Inherited):
            _inherit(program, spec, column)
        else:
            msg = f"unsupported attribute kind for {name!r}: {type(spec).__name__}"
            raise TypeError(msg)


def _synthesize(program: Program, spec: Synthesized, column: list[object]) -> None:
    """Fill a synthesized attribute, children before parents (reverse preorder)."""
    children = program.children
    path_of = program.path_of
    base = spec.base
    combine = spec.combine
    for nid in range(len(program.terms) - 1, -1, -1):
        own = base(program, path_of[nid])
        column[nid] = combine(own, [column[cnid] for cnid in children[nid]])


def _inherit(program: Program, spec: Inherited, column: list[object]) -> None:
    """Fill an inherited attribute, parents before children (preorder)."""
    parent_id = program.parent_id
    path_of = program.path_of
    root = spec.root
    derive = spec.derive
    for nid in range(len(program.terms)):
        parent = parent_id[nid]
        if parent < 0:
            column[nid] = root(program, path_of[nid])
            continue
        path = path_of[nid]
        column[nid] = derive(program, path_of[parent], path[-1], column[parent])
