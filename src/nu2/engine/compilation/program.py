"""Program: an indexed, attributed, compiled Term, ready for a Runtime to drive.

A Program is a flat column store indexed by a dense ``nid: int``. Three
buckets:

- **index** -- ``terms[nid]``, ``children[nid]``, ``parent_id[nid]``,
  ``path_of[nid]``, ``id_of[path]``. Given by the Term's shape.
- **attrs** -- ``attrs[name][nid]``. Computed by schema rules during the
  compile phase.
- **thunks** -- ``thunks[nid]``, ``athunks[nid]``. Per-node closures emitted
  from each Term's ``compile`` / ``acompile`` hook.

The hot path reads columns by nid; path-keyed sugar (``term``, ``kind``,
``payload``, ``parent``, ``walk``, ``attr``) is cold-path.

Construction goes through :func:`nu2.engine.compilation.compile`. Calling
``Program(term, schema)`` directly returns an empty shell -- all columns
start empty -- which is useful only for phase-isolated tests that run
``build_index`` / ``sweep_attributes`` / ``emit_thunks`` themselves.

Access conventions
------------------

The store has two public access tiers:

- **Path-keyed (model API)** -- ``attr(path, name)``, ``walk(under)``.
  Semantic, cold path. Use in rule bodies, validation laws, debugging.
- **nid-keyed (storage API)** -- ``terms[nid]``, ``children[nid]``,
  ``attrs[name][nid]``, ``thunks[nid]``, ... All columns indexed by nid.
  Hot path. The Runtime dispatches via ``thunks[nid](rt)``; predicates
  index directly for speed.

The two are bridged by ``path_of`` (nid -> Path) and ``id_of`` (Path ->
nid); both are public.

Why both: nid lookups are the absolute fastest indexed access (one C-level
list index), with no per-step tuple construction. Path-based access has
to build/hash Path tuples and resolve through ``id_of`` -- fine on the
cold path, prohibitive on the per-node hot loop the Runtime drives.
Storing a dense ``nid`` and dispatching by it is what lets evaluation
avoid allocating during the inner loop.

Truly private: ``_term`` and ``_schema``, used by ``attr`` for declared
resolution and by ``__repr__``.

Other conventions
-----------------

- The root path is ``()``; the root nid is ``0``. Do not use truthiness on
  either: write ``path == program.root`` and ``parent_id[nid] < 0``.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, ClassVar


if TYPE_CHECKING:
    from collections.abc import Awaitable, Callable, Iterator

    from nu2.engine.structure import Schema, Term

__all__ = ["Path", "Program", "UnknownAttributeError"]

type Path = tuple[int, ...]
"""A node's identity: the slot indices along the descent from the root.

Each element is the slot of one descent step (which child of the parent):

- ``()`` is the root itself -- no descent, no slots.
- ``(1,)`` is the root's slot-1 child.
- ``(1, 0)`` is that child's slot-0 child.
- ``(1, 0, 2)`` is that grandchild's slot-2 child, and so on.

A shared Term reached by two different paths is two distinct nodes; each
occurrence has its own Path (and its own ``nid`` in the Program).
"""


class Program:
    """An indexed, attributed, compiled Term, ready for a Runtime to drive."""

    root: ClassVar[Path] = ()

    def __init__(self, term: Term, schema: Schema) -> None:
        # The examples below all assume one running shape -- a minimal DAG
        # with a shared leaf:
        #
        #     x = Literal(7)
        #     description = Add(x, x)
        #
        # The two occurrences of ``x`` get distinct nids (1 and 2) even
        # though they point to the same Term object by identity:
        #
        #     nid 0  Add        path ()
        #     nid 1  Literal(7) path (0,)
        #     nid 2  Literal(7) path (1,)     <-- same Term object as nid 1

        # The root Term of the description, held by reference. The DAG is
        # read off this on every walk; never copied.
        # Example: _term is the Add node; _term.children -> (x, x).
        self._term = term

        # The finalized Schema this Program was compiled against. Read by
        # ``attr`` to resolve declared attributes (which are class constants,
        # not stored in ``attrs``).
        # Example: a schema registering "depth" (inherited) and "size" (synthesized).
        self._schema = schema

        # --- index columns (filled by ``build_index``) -----------------------

        # ``nid -> Term``. The dense list of Terms in preorder; ``terms[0]``
        # is always the root. A shared subtree appears once per occurrence,
        # so two nids may point to the same Term object by identity.
        # Example: [Add, Literal(7), Literal(7)]   (terms[1] is terms[2])
        self.terms: list[Term] = []

        # ``nid -> tuple of child nids``. The structural edge list. Empty
        # tuple at a leaf. Frozen to tuple after the index walk so the public
        # column is immutable.
        # Example: [(1, 2), (), ()]
        self.children: list[tuple[int, ...]] = []

        # ``nid -> parent nid``, or ``-1`` at the root. The ``-1`` sentinel is
        # the only correct "is root" test on an nid (do not use ``if nid``).
        # Example: [-1, 0, 0]
        self.parent_id: list[int] = []

        # ``nid -> Path``. The path-tuple address of each node, used by
        # path-keyed sugar and by rules that need a node's position.
        # Example: [(), (0,), (1,)]
        self.path_of: list[Path] = []

        # ``Path -> nid``. The inverse of ``path_of``; the path-to-nid lookup
        # that backs every path-keyed accessor.
        # Example: {(): 0, (0,): 1, (1,): 2}
        self.id_of: dict[Path, int] = {}

        # --- attribute column store (filled by ``sweep_attributes``) ---------

        # ``name -> per-nid column of values``. One column per *computed*
        # attribute (synthesized or inherited). Declared attributes are
        # class constants and are not stored here; they resolve through the
        # schema on demand inside ``Program.attr``.
        # Example: {"depth": [0, 1, 1], "size": [3, 1, 1]}
        self.attrs: dict[str, list[object]] = {}

        # --- thunk columns (filled by ``emit_thunks``) -----------------------

        # ``nid -> sync evaluator``. The thunk a sync Runtime calls:
        # ``thunks[nid](runtime) -> value``. Each thunk closes over its
        # children's thunks, so dispatch is a single indexed call. Each
        # occurrence of a shared Term gets its own thunk -- ``thunks[1]`` and
        # ``thunks[2]`` are distinct closures, even though ``terms[1]`` and
        # ``terms[2]`` are the same Term.
        # Example: [add_thunk, x_thunk_a, x_thunk_b]
        self.thunks: list[Callable[[object], object]] = []

        # ``nid -> async evaluator``. Async sibling of ``thunks``:
        # ``athunks[nid](runtime) -> awaitable``.
        # Example: [add_athunk, x_athunk_a, x_athunk_b]
        self.athunks: list[Callable[[object], Awaitable[object]]] = []

    # --- structure access ---------------------------------------------------

    def walk(self, under: Path = ()) -> Iterator[Path]:
        """Enumerate every path under ``under`` in preorder, that node first."""
        if under == self.root:
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

        Raises:
            UnknownAttributeError: ``name`` is neither a stored column nor a
                declared attribute on the Term's kind.
        """
        nid = self.id_of[path]
        column = self.attrs.get(name)
        if column is not None:
            return column[nid]
        from nu2.engine.structure.attribute import Declared

        attribute = self._schema.resolve(type(self.terms[nid]), name)
        if not isinstance(attribute, Declared):
            raise UnknownAttributeError(
                f"{type(self.terms[nid]).__name__} has no attribute {name!r}"
            )
        return attribute.value

    def __repr__(self) -> str:
        return f"Program({self._term!r})"


class UnknownAttributeError(KeyError):
    """Raised by :meth:`Program.attr` when an attribute is not on the kind.

    Subclasses :class:`KeyError` so existing ``except KeyError`` sites keep
    working; the message string matches the bare-``KeyError`` text that the
    previous implementation produced.
    """
