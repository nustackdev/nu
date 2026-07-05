"""Act 1: build the index columns of a Program from a Term root.

Iterative preorder walk over the Term DAG read as a tree
(``02-structure.md``). Assigns each occurrence a dense ``nid`` and populates
``terms``, ``children``, ``parent_id``, ``path_of``, ``id_of``. A shared
Term reached by two paths becomes two distinct nids with independent
decoration.
"""

from __future__ import annotations

from typing import TYPE_CHECKING


if TYPE_CHECKING:
    from nu.engine.structure import Term

    from .program import Path, Program

__all__ = ["build_index"]


def build_index(program: Program, root: Term) -> None:
    """Walk ``root`` in preorder; populate the structural columns on ``program``.

    Children are pushed onto the stack in reverse so they pop in slot order;
    each popped node knows its parent's nid and appends itself to that
    parent's child list. Final child lists are frozen into tuples so the
    public column is immutable.
    """
    terms = program.terms
    path_of = program.path_of
    parent_id = program.parent_id
    id_of = program.id_of
    child_lists: list[list[int]] = []

    stack: list[tuple[Term, Path, int]] = [(root, (), -1)]
    while stack:
        node, path, parent_nid = stack.pop()
        nid = len(terms)
        terms.append(node)
        path_of.append(path)
        parent_id.append(parent_nid)
        id_of[path] = nid
        child_lists.append([])
        if parent_nid >= 0:
            child_lists[parent_nid].append(nid)
        term_children = node._children
        for slot in range(len(term_children) - 1, -1, -1):
            stack.append((term_children[slot], (*path, slot), nid))

    program.children = [tuple(c) for c in child_lists]
