"""Context - tagged value store for execution.

The runtime environment the runtime drives an AttributedTerm against. Two axes:

- ``ctx.attrs`` - flat key-value store. Refs read and write here.
- ``bind`` / ``get`` - typed service bindings with scope tags and predicate
  guards. Execution resources (storage, RPC clients, ...) live here.

Bindings are immutable: every ``bind`` / ``lazy`` returns a new Context.
Resolution matches by service type first, then scope tags with subset
fallback; predicate kwargs are evaluated against ``**data`` passed to ``get``.

Usage:
    ctx = Context()
    ctx = ctx.bind(Storage, rocksdb)
    ctx = ctx.bind(Storage, order_db, OrderShape)
    ctx = ctx.bind(View, shard_a, Market,
                   sharding=lambda site, path: site[0] < 16)

    ctx.get(Storage)                                # -> rocksdb
    ctx.get(Storage, OrderShape)                    # -> order_db
    ctx.get(View, Market, site=(5,), path=(...,))   # -> shard_a
"""

from __future__ import annotations

from typing import TYPE_CHECKING, TypeVar, cast


_T = TypeVar("_T")


if TYPE_CHECKING:
    from collections.abc import Callable, Generator

    from .attributes import Attributes


__all__ = ["Context"]


def _name(tag: object) -> str:
    """Human-readable name for a tag."""
    return getattr(tag, "__name__", None) or repr(tag)


# ---------------------------------------------------------------------------
# Entry: the atom of the registry
# ---------------------------------------------------------------------------


class _Entry:
    """One binding - eager (value) or lazy (factory, cached on first access)."""

    __slots__ = ("_factory", "_resolved", "_value", "_was_lazy")

    @staticmethod
    def eager(value: object) -> _Entry:
        """Create an eager (pre-resolved) entry."""
        e = _Entry.__new__(_Entry)
        e._value = value
        e._factory = None
        e._resolved = True
        e._was_lazy = False
        return e

    @staticmethod
    def deferred(factory: Callable[[], object]) -> _Entry:
        """Create a lazy (deferred) entry."""
        e = _Entry.__new__(_Entry)
        e._value = None
        e._factory = factory
        e._resolved = False
        e._was_lazy = True
        return e

    def resolve(self) -> object:
        """Return the value, calling the factory on first access if lazy."""
        if not self._resolved:
            if self._factory is not None:
                self._value = self._factory()
                self._factory = None
            self._resolved = True
        return self._value

    @property
    def was_opened(self) -> bool:
        """True if this was a lazy entry that has been resolved."""
        return self._was_lazy and self._resolved

    @property
    def is_lazy(self) -> bool:
        """True if this entry was registered as lazy (regardless of resolution)."""
        return self._was_lazy


class _GuardedEntry:
    """A predicate-guarded binding. All predicates must pass for a match."""

    __slots__ = ("entry", "predicates", "scope_tags")

    def __init__(
        self,
        scope_tags: frozenset,
        predicates: dict[str, Callable],
        entry: _Entry,
    ) -> None:
        self.scope_tags = scope_tags
        self.predicates = predicates
        self.entry = entry

    def matches(self, data: dict) -> bool:
        """True if all predicates pass with the given data kwargs."""
        return all(pred(**data) for pred in self.predicates.values())


# ---------------------------------------------------------------------------
# Context
# ---------------------------------------------------------------------------


class Context:
    """Tagged value store. The execution address space.

    Bindings have a service type (primary key) and optional scope tags.
    Resolution matches by service type, then scope tags with specificity
    fallback. Named predicate kwargs act as guards evaluated at lookup.
    """

    __slots__ = ("_attrs", "_entries", "_guarded")

    def __init__(self) -> None:
        from .attributes import Attributes

        self._attrs = Attributes()
        self._entries: dict[tuple, _Entry] = {}
        self._guarded: dict[type, list[_GuardedEntry]] = {}

    # -- properties ----------------------------------------------------------

    @property
    def attrs(self) -> Attributes:
        """Flat mutable key-value store for primitive/attribute data."""
        return self._attrs

    # -- write API: type first, always ---------------------------------------

    def bind(
        self,
        service_type: type[_T],
        value: _T,
        *tags: object,
        **predicates: Callable,
    ) -> Context:
        """Bind a value eagerly. Returns new Context.

        Args:
            service_type: Primary key (type).
            value: The value to bind.
            *tags: Scope tags for specificity.
            **predicates: Named guard callables. Each receives **data from get().
        """
        return self._register(
            service_type,
            tags,
            predicates,
            _Entry.eager(value),
        )

    def lazy(
        self,
        service_type: type[_T],
        factory: Callable[[], _T],
        *tags: object,
        **predicates: Callable,
    ) -> Context:
        """Bind a factory lazily. Called on first access, cached. Returns new Context.

        Args:
            service_type: Primary key (type).
            factory: Zero-arg callable that creates the value.
            *tags: Scope tags for specificity.
            **predicates: Named guard callables.
        """
        return self._register(
            service_type,
            tags,
            predicates,
            _Entry.deferred(factory),
        )

    def _register(
        self,
        service_type: type,
        tags: tuple[object, ...],
        predicates: dict[str, Callable],
        entry: _Entry,
    ) -> Context:
        """Shared registration path for bind() and lazy()."""
        scope_tags = frozenset(tags)
        ctx = self._copy()

        if predicates:
            ctx._guarded.setdefault(service_type, []).append(
                _GuardedEntry(scope_tags, dict(predicates), entry),
            )
        else:
            ctx._entries[(service_type, scope_tags)] = entry

        return ctx

    # -- read API: type first, always ----------------------------------------

    def get(self, service_type: type[_T], *tags: object, **data: object) -> _T:
        """Resolve binding by service type + scope tags.

        Args:
            service_type: Primary key (type).
            *tags: Scope tags to match against.
            **data: Passed as **kwargs to all predicates.
        """
        return cast("_T", self._resolve(service_type, frozenset(tags), data))

    def has(self, service_type: type, *tags: object) -> bool:
        """Check if a binding exists for service type + optional scope tags."""
        try:
            self._resolve(service_type, frozenset(tags), {})
        except LookupError:
            return False
        return True

    def was_opened(self, service_type: type, *tags: object) -> bool:
        """Check if a lazy binding was materialized."""
        entry = self._entries.get((service_type, frozenset(tags)))
        return entry is not None and entry.was_opened

    def get_predicates(
        self,
        service_type: type,
        *tags: object,
    ) -> list[tuple[dict, object]]:
        """Get all predicate entries for a service type + tags.

        Returns list of (predicates_dict, value) for each guarded entry
        matching the exact tag set.
        """
        guarded = self._guarded.get(service_type, [])
        scope_tags = frozenset(tags)
        result: list[tuple[dict, object]] = []
        for g in guarded:
            if g.scope_tags == scope_tags:
                result.append((dict(g.predicates), g.entry.resolve()))
        return result

    # -- resolution ----------------------------------------------------------

    def _resolve(
        self,
        service_type: type,
        scope_tags: frozenset,
        data: dict,
    ) -> object:
        """Core resolution with specificity fallback.

        1. Try exact scope tags match.
        2. Subset fallback: try progressively smaller scope tag sets.
        3. Empty scope fallback.
        """
        entry = self._find(service_type, scope_tags, data)
        if entry is not None:
            return entry.resolve()

        if len(scope_tags) > 1:
            tags_list = sorted(scope_tags, key=id)
            for size in range(len(scope_tags) - 1, 0, -1):
                for subset in _subsets_of_size(tags_list, size):
                    entry = self._find(service_type, frozenset(subset), data)
                    if entry is not None:
                        return entry.resolve()

        if scope_tags:
            entry = self._find(service_type, frozenset(), data)
            if entry is not None:
                return entry.resolve()

        tag_names = ", ".join(_name(t) for t in scope_tags)
        data_str = ", ".join(f"{k}={v!r}" for k, v in data.items())
        parts = [_name(service_type)]
        if tag_names:
            parts.append(f"[{tag_names}]")
        if data_str:
            parts.append(f"({data_str})")
        msg = f"No binding for: {''.join(parts)}"
        raise LookupError(msg)

    def _find(
        self,
        service_type: type,
        scope_tags: frozenset,
        data: dict,
    ) -> _Entry | None:
        """Find entry at exact scope level. Returns None if nothing found.

        If guarded entries exist for this service_type with matching scope,
        predicates are evaluated. All predicates on an entry must pass (AND).
        At least one entry must fully match (OR across entries).
        No fallback to non-predicate bindings at same scope if guarded exist.
        """
        guarded = self._guarded.get(service_type) if data else None
        if guarded:
            candidates = [g for g in guarded if g.scope_tags == scope_tags]
            if candidates:
                for g in candidates:
                    if g.matches(data):
                        return g.entry
                return None

        return self._entries.get((service_type, scope_tags))

    # -- copy ----------------------------------------------------------------

    def _copy(self) -> Context:
        """Shallow copy. Attrs are deep-copied so mutations don't leak."""
        ctx = Context.__new__(Context)
        ctx._attrs = self._attrs.copy()
        ctx._entries = dict(self._entries)
        ctx._guarded = {k: list(v) for k, v in self._guarded.items()}
        return ctx

    # -- repr ----------------------------------------------------------------

    def __repr__(self) -> str:
        parts: list[str] = []
        for (stype, stags), entry in self._entries.items():
            labels = [_name(stype), *(_name(t) for t in stags)]
            if entry.is_lazy:
                labels.append("lazy")
            parts.append("+".join(labels))
        for stype, entries in self._guarded.items():
            for g in entries:
                labels = [_name(stype), *(_name(t) for t in g.scope_tags)]
                labels.append("+".join(g.predicates))
                parts.append("+".join(labels))
        return f"Context({', '.join(parts)})"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _subsets_of_size(items: list, size: int) -> Generator[tuple, None, None]:
    """Generate all subsets of a given size from items."""
    if size == 0:
        yield ()
        return
    for i in range(len(items)):
        for rest in _subsets_of_size(items[i + 1 :], size - 1):
            yield (items[i], *rest)
