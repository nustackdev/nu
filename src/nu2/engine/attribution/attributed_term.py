"""AttributedTerm: a description plus the attr relation, as flat columns.

Attribution unfolds the description DAG into a tree of positions and assigns
each position a dense ``nid: int`` in preorder. All state is held as columns
indexed by ``nid``:

- ``terms[nid]``      - the Term at that position (a Term may repeat across nids)
- ``kids[nid]``       - tuple of child nids
- ``parent_id[nid]``  - parent nid, ``-1`` at the root
- ``path_of[nid]``    - the Path for that position (cold-path / queries)
- ``id_of[path]``     - inverse of ``path_of``
- ``attrs[name][nid]``- one column per computed attribute, list indexed by nid

The hot path reads columns directly. Path-based methods are O(1) sugar around
``id_of`` for predicate, sweep and query code that speaks in paths. Declared
attributes are not stored - they are class constants resolved via the schema
on demand by ``_read``.

The top-level entry is ``attribute(description, schema)``: build the index,
then run a sweep per computed attribute in schema-finalized order. The two
sweeps (synthesized bottom-up, inherited top-down) live below as free
functions; they are the attribution algorithm.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from nu2.engine.attribution.attr import Attr


if TYPE_CHECKING:
    from collections.abc import Callable, Iterator

    from nu2.engine.structure.attribute import Attribute, Schema
    from nu2.engine.structure.term import Term

__all__ = ["AttributedTerm", "Path", "attribute"]

type Path = tuple[int, ...]


class AttributedTerm:
    """An attributed Nu program: held description plus flat attribute columns."""

    root: Path = ()

    def __init__(self, description: Term, schema: Schema) -> None:
        self._description = description
        self._schema = schema
        # Structural columns, populated by the index build below.
        self.terms: list[Term] = []
        self.kids: list[tuple[int, ...]] = []
        self.parent_id: list[int] = []
        self.path_of: list[Path] = []
        self.id_of: dict[Path, int] = {}
        # Attribute columns; one entry per computed attribute after the sweep.
        self.attrs: dict[str, list[object]] = {}
        # Compiled per-nid thunks: each takes a Runtime, returns the node's
        # value (sync) or an awaitable of it (async). Populated by
        # ``_compile`` at the end of ``attribute``.
        self.thunks: list[Callable] = []
        self.athunks: list[Callable] = []
        self.attr = Attr(self)
        self._build_index(description)

    # --- index build --------------------------------------------------------

    def _build_index(self, root: Term) -> None:
        """Iterative preorder walk: assign nids and populate structural columns.

        Children are pushed onto the stack in reverse so they pop in slot
        order; each popped node knows its parent's nid and appends itself to
        that parent's kid list. Final kid lists are frozen into tuples.
        """
        terms = self.terms
        path_of = self.path_of
        parent_id = self.parent_id
        id_of = self.id_of
        kid_lists: list[list[int]] = []

        stack: list[tuple[Term, Path, int]] = [(root, (), -1)]
        while stack:
            node, path, parent_nid = stack.pop()
            nid = len(terms)
            terms.append(node)
            path_of.append(path)
            parent_id.append(parent_nid)
            id_of[path] = nid
            kid_lists.append([])
            if parent_nid >= 0:
                kid_lists[parent_nid].append(nid)
            children = node.children
            for slot in range(len(children) - 1, -1, -1):
                stack.append((children[slot], (*path, slot), nid))

        self.kids = [tuple(k) for k in kid_lists]

    # --- structure ----------------------------------------------------------

    def term(self, path: Path) -> Term:
        """The Term at ``path``."""
        return self.terms[self.id_of[path]]

    def kind(self, path: Path) -> type[Term]:
        """The kind (class) of the Term at ``path``."""
        return type(self.terms[self.id_of[path]])

    def payload(self, path: Path) -> dict[str, object]:
        """The payload of the Term at ``path``."""
        return self.terms[self.id_of[path]].payload

    def parent(self, path: Path) -> Path | None:
        """The parent path, or ``None`` at the root."""
        return path[:-1] if path else None

    def children(self, path: Path) -> list[Path]:
        """The child paths of ``path``."""
        path_of = self.path_of
        return [path_of[cnid] for cnid in self.kids[self.id_of[path]]]

    def walk(self, under: Path = ()) -> Iterator[Path]:
        """Enumerate every path under ``under`` in preorder, that node first."""
        if under == ():
            yield from self.path_of
            return
        start = self.id_of[under]
        yield self.path_of[start]
        for cnid in self.kids[start]:
            yield from self._walk_nid(cnid)

    def _walk_nid(self, nid: int) -> Iterator[Path]:
        yield self.path_of[nid]
        for cnid in self.kids[nid]:
            yield from self._walk_nid(cnid)

    # --- compile ------------------------------------------------------------

    def _compile(self) -> None:
        """Build the per-nid sync and async thunk columns, children before parents.

        Each ``Term.compile`` / ``Term.acompile`` receives its node's compiled
        child thunks and returns a thunk that evaluates the subtree. The
        reverse-preorder walk (``n - 1`` down to ``0``) guarantees a child's
        thunk is in hand by the time its parent is compiled.
        """
        terms = self.terms
        kids_col = self.kids
        n = len(terms)
        thunks: list[Callable] = [None] * n  # type: ignore[list-item]
        athunks: list[Callable] = [None] * n  # type: ignore[list-item]
        for nid in range(n - 1, -1, -1):
            kids = kids_col[nid]
            kid_thunks = tuple(thunks[k] for k in kids)
            kid_athunks = tuple(athunks[k] for k in kids)
            term = terms[nid]
            thunks[nid] = term.compile(nid, kid_thunks)
            athunks[nid] = term.acompile(nid, kid_athunks)
        self.thunks = thunks
        self.athunks = athunks

    # --- attribute read -----------------------------------------------------

    def _read(self, path: Path, name: str) -> object:
        """Read attribute ``name`` at ``path``.

        Computed attributes live in ``attrs`` (one dict get + one list index).
        Declared attributes are class constants resolved via the schema.
        """
        nid = self.id_of[path]
        column = self.attrs.get(name)
        if column is not None:
            return column[nid]
        attribute = self._schema.attribute(type(self.terms[nid]), name)
        if attribute is None:
            raise KeyError(f"{type(self.terms[nid]).__name__} has no attribute {name!r}")
        if attribute.flavor == "declared":
            return attribute.value
        raise KeyError(f"{type(self.terms[nid]).__name__} attribute {name!r} not populated")

    def __repr__(self) -> str:
        return f"AttributedTerm({self._description!r}, {self.attr!r})"


# --- attribution: factory + sweeps -----------------------------------------


def attribute(description: Term, schema: Schema) -> AttributedTerm:
    """Build an AttributedTerm and run every computed attribute sweep.

    Args:
        description: the root Term of the application.
        schema: a finalized Schema.

    Returns:
        An AttributedTerm with every computed column populated. Declared
        attributes are not stored; they read through the schema on demand.
    """
    program = AttributedTerm(description, schema)
    n = len(program.terms)
    for name in schema.order():
        spec = schema._global[name]
        column: list[object] = [None] * n
        program.attrs[name] = column
        if spec.flavor == "synthesized":
            _synthesize(program, spec, column)
        else:
            _inherit(program, spec, column)
    program._compile()
    return program


def _synthesize(program: AttributedTerm, spec: Attribute, column: list[object]) -> None:
    """Fill a synthesized attribute, children before parents (reverse preorder)."""
    kids = program.kids
    path_of = program.path_of
    base = spec.base
    combine = spec.combine
    for nid in range(len(program.terms) - 1, -1, -1):
        own = base(program, path_of[nid])
        column[nid] = combine(own, [column[cnid] for cnid in kids[nid]])


def _inherit(program: AttributedTerm, spec: Attribute, column: list[object]) -> None:
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
