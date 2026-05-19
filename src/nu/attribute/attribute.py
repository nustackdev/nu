"""Attribute and Schema: the named values on Symbol classes, and the registry.

An Attribute is a named value attached to a kind, in one of three flavors:
declared (a constant), synthesized (folded bottom-up), inherited (threaded
top-down). A Schema holds the tree-wide attributes and, at finalize, builds
and topologically sorts the cross-attribute dependency graph.
"""

from __future__ import annotations

from typing import TYPE_CHECKING


if TYPE_CHECKING:
    from collections.abc import Callable
    from typing import Literal

    from nu.attribute.symbol import Symbol

__all__ = ["Attribute", "CycleError", "Flavor", "RuleFn", "Schema"]

type Flavor = Literal["declared", "synthesized", "inherited"]
type RuleFn = Callable[..., object]


class CycleError(Exception):
    """Raised when the attribute dependency graph contains a cycle."""


class Attribute:
    """A named value on a Symbol class, in one of three flavors.

    declared: a constant, read straight off the class. synthesized: an own
    value via ``base``, folded with children by ``combine``. inherited: a
    value via ``root`` at the root, else via ``derive`` from the parent.

    The computed flavors carry ``reads``: the names of the attributes their
    rules consult, the edges of the dependency graph.
    """

    def __init__(
        self,
        flavor: Flavor,
        name: str | None = None,
        *,
        value: object = None,
        reads: tuple[str, ...] = (),
        base: RuleFn | None = None,
        combine: RuleFn | None = None,
        root: RuleFn | None = None,
        derive: RuleFn | None = None,
    ) -> None:
        self.flavor = flavor
        self.name = name
        self.value = value
        self.reads = reads
        self.base = base
        self.combine = combine
        self.root = root
        self.derive = derive

    @classmethod
    def declared(cls, value: object, name: str | None = None) -> Attribute:
        """A constant attribute, read straight off the class."""
        return cls("declared", name, value=value)

    @classmethod
    def synthesized(
        cls,
        name: str,
        base: RuleFn,
        combine: RuleFn,
        *,
        reads: tuple[str, ...] = (),
    ) -> Attribute:
        """A bottom-up attribute: own value via ``base``, folded with ``combine``."""
        return cls("synthesized", name, base=base, combine=combine, reads=reads)

    @classmethod
    def inherited(
        cls,
        name: str,
        root: RuleFn,
        derive: RuleFn,
        *,
        reads: tuple[str, ...] = (),
    ) -> Attribute:
        """A top-down attribute: ``root`` at the root, ``derive`` below it."""
        return cls("inherited", name, root=root, derive=derive, reads=reads)

    def __repr__(self) -> str:
        return f"Attribute({self.flavor!r}, {self.name!r})"


class Schema:
    """The tree-wide attributes plus the finalized dependency order.

    Per-class declared attributes live on the Symbol classes themselves,
    collected by SymbolMeta. Computed attributes (synthesized, inherited) are
    registered here, tree-wide. ``finalize`` builds and topologically sorts
    the cross-attribute dependency graph; a cycle raises CycleError.

    The attribute layer never owns a Schema instance. A layer-1 language builds one,
    registers its attributes, finalizes it once, and never mutates it again.
    """

    def __init__(self) -> None:
        self._global: dict[str, Attribute] = {}
        self._order: list[str] | None = None

    def register(self, attribute: Attribute) -> None:
        """Register a tree-wide attribute; invalidates any prior finalize."""
        if attribute.name is None:
            raise ValueError("a registered attribute must have a name")
        self._global[attribute.name] = attribute
        self._order = None

    def attribute(self, kind: type[Symbol], name: str) -> Attribute | None:
        """Resolve an attribute for a kind: per-class first, then tree-wide."""
        per_class = kind._attributes.get(name)
        if per_class is not None:
            return per_class
        return self._global.get(name)

    def finalize(self) -> Schema:
        """Build and topologically sort the dependency graph.

        Returns:
            This schema, for chaining.

        Raises:
            CycleError: if the cross-attribute dependency graph has a cycle.
        """
        computed = {name: attr for name, attr in self._global.items() if attr.flavor != "declared"}
        order: list[str] = []
        state: dict[str, int] = {}  # name -> 0 visiting, 1 done

        def visit(name: str) -> None:
            """Depth-first visit for the topological sort."""
            mark = state.get(name)
            if mark == 1:
                return
            if mark == 0:
                raise CycleError(f"cyclic attribute dependency at {name!r}")
            state[name] = 0
            for dep in computed[name].reads:
                if dep in computed:
                    visit(dep)
            state[name] = 1
            order.append(name)

        for name in computed:
            visit(name)
        self._order = order
        return self

    def order(self) -> list[str]:
        """The topological order of computed attributes; requires finalize."""
        if self._order is None:
            raise RuntimeError("schema is not finalized; call finalize() first")
        return self._order
