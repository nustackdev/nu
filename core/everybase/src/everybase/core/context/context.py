"""Context — tagged value store for execution.

Context is the runtime environment passed to Executable.execute().
It holds bindings keyed by tag sets with specificity-based resolution.

Design:
    - Immutable: bind() returns new Context
    - Tag-keyed: values looked up by tag sets with subset fallback
    - Lazy factories: values can be created on-demand
    - Any hashable can be a tag (type, string, Shape, etc.)
"""

from __future__ import annotations

from typing import TYPE_CHECKING


if TYPE_CHECKING:
    from collections.abc import Callable, Generator


__all__ = [
    "Context",
]


class Context:
    """Tagged value store. The execution address space.

    Bindings have tags. Resolution matches by tags.
    More tags = more specific. Fallback = fewer tags.

    Usage:
        ctx = Context()
        ctx = ctx.bind(rocksdb, Storage)                  # 1 tag
        ctx = ctx.bind(order_db, Storage, OrderShape)      # 2 tags
        ctx = ctx.bind("timeout", "error")                 # name tag

        ctx[Storage]                    # → rocksdb
        ctx[Storage, OrderShape]        # → order_db
        ctx["error"]                    # → "timeout"
    """

    def __init__(self) -> None:
        """Initialize empty context."""
        self._bindings: dict[frozenset, object] = {}
        self._factories: dict[frozenset, Callable] = {}
        self._opened: set[frozenset] = set()

    def _copy(self) -> Context:
        """Create a shallow copy."""
        ctx = Context.__new__(Context)
        ctx._bindings = dict(self._bindings)
        ctx._factories = dict(self._factories)
        ctx._opened = set(self._opened)
        return ctx

    @staticmethod
    def _normalize(tags: tuple) -> frozenset:
        """Normalize tags to frozenset."""
        return frozenset(tags)

    def bind(self, value: object, *tags: object) -> Context:
        """Bind value to tag set. Returns new Context (immutable).

        Args:
            value: The value to bind.
            *tags: One or more tags (types, strings, etc.).

        Returns:
            New Context with the binding added.
        """
        if not tags:
            msg = "bind() requires at least one tag"
            raise ValueError(msg)
        key = self._normalize(tags)
        ctx = self._copy()
        ctx._bindings[key] = value
        ctx._factories.pop(key, None)
        return ctx

    def lazy(self, factory: Callable, *tags: object) -> Context:
        """Bind lazy factory to tag set. Called on first access, cached.

        Args:
            factory: Callable that creates the value.
            *tags: One or more tags.

        Returns:
            New Context with the factory added.
        """
        if not tags:
            msg = "lazy() requires at least one tag"
            raise ValueError(msg)
        key = self._normalize(tags)
        ctx = self._copy()
        ctx._factories[key] = factory
        return ctx

    def has(self, *tags: object) -> bool:
        """Check if binding exists for exact tag set."""
        key = self._normalize(tags)
        return key in self._bindings or key in self._factories

    def was_opened(self, *tags: object) -> bool:
        """Check if lazy binding was materialized."""
        key = self._normalize(tags)
        return key in self._opened

    def _resolve(self, key: frozenset) -> object:
        """Resolve a frozenset key with specificity fallback.

        Resolution order:
        1. Exact match in bindings
        2. Exact match in factories (create + cache)
        3. Largest subset match, then smaller subsets
        4. LookupError if nothing found
        """
        # Exact match — bindings
        if key in self._bindings:
            return self._bindings[key]

        # Exact match — factory
        if key in self._factories:
            value = self._factories[key]()
            self._bindings[key] = value
            self._opened.add(key)
            return value

        # Subset fallback: try subsets from largest to smallest
        if len(key) > 1:
            for size in range(len(key) - 1, 0, -1):
                # Generate subsets of this size
                tags_list = sorted(key, key=id)
                for subset in _subsets_of_size(tags_list, size):
                    fset = frozenset(subset)
                    if fset in self._bindings:
                        return self._bindings[fset]
                    if fset in self._factories:
                        value = self._factories[fset]()
                        self._bindings[fset] = value
                        self._opened.add(fset)
                        return value

        # Nothing found
        tag_names = ", ".join(t.__name__ if hasattr(t, "__name__") else repr(t) for t in key)
        msg = f"No binding for tags: {tag_names}"
        raise LookupError(msg)

    def __getitem__(self, tags: object) -> object:
        """Resolve by tags with specificity fallback.

        Usage:
            ctx[StorageProtocol]              # single tag
            ctx[StorageProtocol, OrderShape]   # multiple tags
            ctx["error"]                       # string tag
        """
        if not isinstance(tags, tuple):
            tags = (tags,)
        return self._resolve(frozenset(tags))

    def __contains__(self, tags: object) -> bool:
        """Check if tags resolve (including subset fallback)."""
        if not isinstance(tags, tuple):
            tags = (tags,)
        try:
            self._resolve(frozenset(tags))
        except LookupError:
            return False
        return True

    def __repr__(self) -> str:
        """String representation."""
        parts = []
        for key in self._bindings:
            labels = [t.__name__ if hasattr(t, "__name__") else repr(t) for t in key]
            parts.append("+".join(labels))
        for key in self._factories:
            if key not in self._bindings:
                labels = [t.__name__ if hasattr(t, "__name__") else repr(t) for t in key]
                parts.append(f"{'+'.join(labels)}(lazy)")
        return f"Context({', '.join(parts)})"


def _subsets_of_size(items: list, size: int) -> Generator[tuple, None, None]:
    """Generate all subsets of a given size from items."""
    if size == 0:
        yield ()
        return
    for i in range(len(items)):
        for rest in _subsets_of_size(items[i + 1 :], size - 1):
            yield (items[i], *rest)
