"""Program: an indexed, attributed, compiled Term, ready for a Runtime.

Compilation produces this. A ``Term`` goes in; a ``Program`` comes out. Inside
it holds three buckets, all flat columns indexed by a dense ``nid: int``:

- index   - ``terms[nid]``, ``children[nid]``, ``parent_id[nid]``,
            ``path_of[nid]``, ``id_of[path]``. Given by the Term's shape.
- attrs   - ``attrs[name][nid]``. Computed by schema rules.
- thunks  - ``thunks[nid]``, ``athunks[nid]``. Closures emitted from each
            Term's ``compile`` / ``acompile`` hook, capturing child thunks.

Hot path reads columns by nid; path-keyed sugar (``term``, ``kind``, ``attr``,
``walk``) is cold-path.

The top-level entry is ``compile(term, schema)``: build the index, run a
sweep per computed attribute in finalized order, then emit the thunk
columns. The two sweep helpers live below as free functions.
"""

from __future__ import annotations

from typing import TYPE_CHECKING


if TYPE_CHECKING:
    from collections.abc import Callable, Iterator

    from nu2.engine.structure.attribute import Attribute, Schema
    from nu2.engine.structure.term import Term

__all__ = ["Path", "Program", "compile"]

type Path = tuple[int, ...]


class Program:
    """An indexed, attributed, compiled Term, ready for a Runtime to drive."""

    root: Path = ()

    def __init__(self, term: Term, schema: Schema) -> None:
        self._term = term
        self._schema = schema
        # index
        self.terms: list[Term] = []
        self.children: list[tuple[int, ...]] = []
        self.parent_id: list[int] = []
        self.path_of: list[Path] = []
        self.id_of: dict[Path, int] = {}
        # attrs (populated by the compile phase)
        self.attrs: dict[str, list[object]] = {}
        # thunks (populated by the emit pass at the end of compile)
        self.thunks: list[Callable] = []
        self.athunks: list[Callable] = []
        self._build_index(term)

    # --- index build --------------------------------------------------------

    def _build_index(self, root: Term) -> None:
        """Iterative preorder walk: assign nids, populate the index columns.

        Children are pushed onto the stack in reverse so they pop in slot
        order; each popped node knows its parent's nid and appends itself to
        that parent's child list. Final child lists are frozen into tuples.
        """
        terms = self.terms
        path_of = self.path_of
        parent_id = self.parent_id
        id_of = self.id_of
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
            term_children = node.children
            for slot in range(len(term_children) - 1, -1, -1):
                stack.append((term_children[slot], (*path, slot), nid))

        self.children = [tuple(c) for c in child_lists]

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

    def walk(self, under: Path = ()) -> Iterator[Path]:
        """Enumerate every path under ``under`` in preorder, that node first."""
        if under == ():
            yield from self.path_of
            return
        start = self.id_of[under]
        yield self.path_of[start]
        for cnid in self.children[start]:
            yield from self._walk_nid(cnid)

    def _walk_nid(self, nid: int) -> Iterator[Path]:
        yield self.path_of[nid]
        for cnid in self.children[nid]:
            yield from self._walk_nid(cnid)

    # --- attribute access ---------------------------------------------------

    def attr(self, path: Path, name: str) -> object:
        """Read attribute ``name`` at ``path``.

        Computed attributes live in ``attrs`` (one dict get + one list index).
        Declared attributes are class constants resolved via the schema. The
        hot path skips this and reads ``program.attrs[name][nid]`` directly.
        """
        nid = self.id_of[path]
        column = self.attrs.get(name)
        if column is not None:
            return column[nid]
        attribute = self._schema.attribute(type(self.terms[nid]), name)
        if attribute is None or attribute.flavor != "declared":
            raise KeyError(f"{type(self.terms[nid]).__name__} has no attribute {name!r}")
        return attribute.value

    # --- emit ---------------------------------------------------------------

    def _emit(self) -> None:
        """Build the per-nid sync and async thunk columns, children before parents.

        Each ``Term.compile`` / ``Term.acompile`` receives its node's compiled
        child thunks and returns a thunk that evaluates the subtree. The
        reverse-preorder walk (``n - 1`` down to ``0``) guarantees a child's
        thunk is in hand by the time its parent is compiled.
        """
        terms = self.terms
        children = self.children
        n = len(terms)
        thunks: list[Callable] = [None] * n  # type: ignore[list-item]
        athunks: list[Callable] = [None] * n  # type: ignore[list-item]
        for nid in range(n - 1, -1, -1):
            child_nids = children[nid]
            child_thunks = tuple(thunks[c] for c in child_nids)
            child_athunks = tuple(athunks[c] for c in child_nids)
            term = terms[nid]
            thunks[nid] = term.compile(nid, child_thunks)
            athunks[nid] = term.acompile(nid, child_athunks)
        self.thunks = thunks
        self.athunks = athunks

    def __repr__(self) -> str:
        return f"Program({self._term!r})"


# --- compile phase ----------------------------------------------------------


def compile(term: Term, schema: Schema) -> Program:
    """Compile a Term against a finalized Schema: index, attribute, emit.

    Args:
        term: the root Term of the description.
        schema: a finalized Schema.

    Returns:
        A Program with every computed attribute column populated and the
        thunk columns emitted. Declared attributes are not stored; they read
        through the schema on demand via ``Program.attr``.
    """
    program = Program(term, schema)
    n = len(program.terms)
    for name in schema.order():
        spec = schema._global[name]
        column: list[object] = [None] * n
        program.attrs[name] = column
        if spec.flavor == "synthesized":
            _synthesize(program, spec, column)
        else:
            _inherit(program, spec, column)
    program._emit()
    return program


def _synthesize(program: Program, spec: Attribute, column: list[object]) -> None:
    """Fill a synthesized attribute, children before parents (reverse preorder)."""
    children = program.children
    path_of = program.path_of
    base = spec.base
    combine = spec.combine
    for nid in range(len(program.terms) - 1, -1, -1):
        own = base(program, path_of[nid])
        column[nid] = combine(own, [column[cnid] for cnid in children[nid]])


def _inherit(program: Program, spec: Attribute, column: list[object]) -> None:
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
