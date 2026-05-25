"""Schema: the tree-wide attribute registry and dependency order.

A schema is the engine's view of a layer-1 language's attribute set. Per-class
declared attributes live on the Term classes themselves, collected by
:class:`~nu2.engine.structure.term.TermMeta`. Tree-wide attributes -- defaults
and every computed attribute -- are registered here.

Lifecycle: build, register, finalize, use. ``finalize`` builds and
topologically sorts the cross-attribute dependency graph; once finalized the
schema is read-only in practice. A cycle in the graph raises
:class:`~nu2.engine.structure.exceptions.CycleError`; using a non-finalized
schema raises :class:`~nu2.engine.structure.exceptions.NotFinalizedError`.

The engine never owns a schema instance. A layer-1 language builds one,
registers its attributes, and finalizes it once at import.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from nu2.engine.structure.exceptions import CycleError, NotFinalizedError


if TYPE_CHECKING:
    from nu2.engine.structure.attribute import Attribute
    from nu2.engine.structure.term import Term

__all__ = ["Schema"]


class Schema:
    """The tree-wide attribute registry plus the finalized dependency order."""

    def __init__(self) -> None:
        self._registered: dict[str, Attribute] = {}
        self._topo_order: list[str] | None = None

    # --- registration -------------------------------------------------------

    def register(self, attribute: Attribute) -> None:
        """Register a tree-wide attribute.

        Invalidates any prior :meth:`finalize`.

        Raises:
            ValueError: if the attribute has no name.
        """
        if attribute.name is None:
            msg = "a registered attribute must have a name"
            raise ValueError(msg)
        self._registered[attribute.name] = attribute
        self._topo_order = None

    def __contains__(self, name: str) -> bool:
        return name in self._registered

    def __getitem__(self, name: str) -> Attribute:
        """Look up a tree-wide attribute by name.

        Raises:
            KeyError: if no attribute with ``name`` is registered.
        """
        return self._registered[name]

    # --- resolution ---------------------------------------------------------

    def resolve(self, kind: type[Term], name: str) -> Attribute | None:
        """Resolve an attribute for a Term ``kind`` by ``name``.

        Per-class declarations take precedence over tree-wide ones; the
        class wins where it overrides a default. Returns ``None`` if neither
        defines the attribute.
        """
        per_class = kind.attributes.get(name)
        if per_class is not None:
            return per_class
        return self._registered.get(name)

    # --- finalize -----------------------------------------------------------

    def finalize(self) -> Schema:
        """Build and topologically sort the dependency graph.

        Returns:
            This schema, for chaining.

        Raises:
            CycleError: the cross-attribute dependency graph has a cycle.
        """
        from nu2.engine.structure.attribute import Computed

        computed: dict[str, Computed] = {
            name: attr for name, attr in self._registered.items() if isinstance(attr, Computed)
        }
        order: list[str] = []
        # name -> mark; absent: unseen, 0: on the current path, 1: done.
        visiting, done = 0, 1
        state: dict[str, int] = {}

        def visit(name: str) -> None:
            mark = state.get(name)
            if mark == done:
                return
            if mark == visiting:
                msg = f"cyclic attribute dependency at {name!r}"
                raise CycleError(msg)
            state[name] = visiting
            for dep in computed[name].reads:
                if dep in computed:
                    visit(dep)
            state[name] = done
            order.append(name)

        for name in computed:
            visit(name)
        self._topo_order = order
        return self

    def topo_order(self) -> list[str]:
        """Names of the computed attributes in topological order.

        Returns:
            The order in which compile sweeps the attributes -- every
            attribute's ``reads`` are scheduled before it.

        Raises:
            NotFinalizedError: if :meth:`finalize` has not been called.
        """
        if self._topo_order is None:
            msg = "schema is not finalized; call finalize() first"
            raise NotFinalizedError(msg)
        return self._topo_order
