"""Context -- tagged value store for execution.

Context is the runtime environment passed to Executable.execute().
It holds bindings keyed by service type + scope tags, with specificity-based
resolution and optional named predicate guards.

Design:
    - Immutable: bind() returns new Context
    - Service-type keyed: first argument after value is always the service type
    - Scope tags: additional tags for specificity (Shape classes, strings, etc.)
    - Named predicates: kwargs in bind() define guards, kwargs in get() pass data
    - Lazy factories: values can be created on-demand
    - Specificity fallback: more scope tags = more specific, subset fallback

Resolution:
    1. If guarded entries exist for (service_type, scope_tags), evaluate all
       predicates with **data from get(). At least one entry must fully match.
    2. If no guarded entries, fast dict lookup in _bindings/_factories.
    3. Subset fallback: try smaller scope tag sets with same logic.
"""

from __future__ import annotations

from typing import TYPE_CHECKING


if TYPE_CHECKING:
    from collections.abc import Callable, Generator

    from .attributes import Attributes


__all__ = [
    "Context",
]


def _name(tag: object) -> str:
    """Human-readable name for a tag."""
    return tag.__name__ if hasattr(tag, "__name__") else repr(tag)


class Context:
    """Tagged value store. The execution address space.

    Bindings have a service type (primary key) and optional scope tags.
    Resolution matches by service type, then scope tags with specificity
    fallback. Named predicate kwargs act as guards evaluated at lookup.

    Usage:
        ctx = Context()
        ctx = ctx.bind(rocksdb, Storage)                          # type only
        ctx = ctx.bind(order_db, Storage, OrderShape)              # type + scope
        ctx = ctx.bind("timeout", "error")                         # string key
        ctx = ctx.bind(shard_a, View, Market,                      # predicate
                        sharding=lambda site, path: site[0] < 16)

        ctx[Storage]                                   # -> rocksdb
        ctx[Storage, OrderShape]                       # -> order_db
        ctx["error"]                                   # -> "timeout"
        ctx.get(View, Market, site=(5,), path=(...,))  # -> shard_a
    """

    __slots__ = ("_attrs", "_bindings", "_factories", "_guarded", "_opened")

    def __init__(self) -> None:
        """Initialize empty context."""
        from .attributes import Attributes

        self._attrs = Attributes()
        self._bindings: dict[tuple, object] = {}
        self._factories: dict[tuple, Callable] = {}
        self._opened: set[tuple] = set()
        # service_type -> [(scope_tags, preds_dict, value, factory), ...]
        self._guarded: dict[object, list[tuple]] = {}

    @property
    def attrs(self) -> Attributes:
        """Flat mutable key-value store for primitive/attribute data."""
        return self._attrs

    def _copy(self) -> Context:
        """Create a shallow copy. Attrs are copied so mutations don't leak."""
        ctx = Context.__new__(Context)
        ctx._attrs = self._attrs.copy()
        ctx._bindings = dict(self._bindings)
        ctx._factories = dict(self._factories)
        ctx._opened = set(self._opened)
        ctx._guarded = {k: list(v) for k, v in self._guarded.items()}
        return ctx

    def bind(
        self, value: object, service_type: object, *tags: object, **predicates: Callable
    ) -> Context:
        """Bind value to service type + tags. Returns new Context.

        Args:
            value: The value to bind.
            service_type: Primary key (type, string, etc.).
            *tags: Scope tags for specificity.
            **predicates: Named guard callables. Each receives **data from get().

        Returns:
            New Context with the binding added.
        """
        scope_tags = frozenset(tags)
        ctx = self._copy()

        if predicates:
            ctx._guarded.setdefault(service_type, []).append(
                (scope_tags, dict(predicates), value, None)
            )
        else:
            key = (service_type, scope_tags)
            ctx._bindings[key] = value
            ctx._factories.pop(key, None)

        return ctx

    def lazy(
        self, factory: Callable, service_type: object, *tags: object, **predicates: Callable
    ) -> Context:
        """Bind lazy factory. Called on first access, cached.

        Args:
            factory: Zero-arg callable that creates the value.
            service_type: Primary key (type, string, etc.).
            *tags: Scope tags for specificity.
            **predicates: Named guard callables.

        Returns:
            New Context with the factory added.
        """
        scope_tags = frozenset(tags)
        ctx = self._copy()

        if predicates:
            ctx._guarded.setdefault(service_type, []).append(
                (scope_tags, dict(predicates), None, factory)
            )
        else:
            key = (service_type, scope_tags)
            ctx._factories[key] = factory

        return ctx

    def get(self, service_type: object, *tags: object, **data: object) -> object:
        """Resolve with optional predicate data.

        Args:
            service_type: Primary key.
            *tags: Scope tags to match against.
            **data: Passed as **kwargs to all predicates.

        Returns:
            The resolved value.
        """
        return self._resolve(service_type, frozenset(tags), data)

    def has(self, service_type: object, *tags: object) -> bool:
        """Check if a binding exists for service type + tags."""
        try:
            self._resolve(service_type, frozenset(tags), {})
        except LookupError:
            return False
        return True

    def get_predicates(
        self,
        service_type: object,
        *tags: object,
    ) -> list[tuple[dict, object]]:
        """Get all predicate entries for a service type + tags.

        Returns list of (predicates_dict, value) for each guarded entry
        matching the exact tag set. Used by spans that need to replicate
        predicate bindings onto derived types (e.g. Atomic binding View
        with same predicates as Navigator).

        Returns empty list if no guarded entries exist.
        """
        guarded = self._guarded.get(service_type, [])
        scope_tags = frozenset(tags)
        result = []
        for etags, preds, val, fac in guarded:
            if etags == scope_tags:
                v = val if fac is None else fac()
                result.append((dict(preds), v))
        return result

    def was_opened(self, service_type: object, *tags: object) -> bool:
        """Check if a lazy binding was materialized."""
        return (service_type, frozenset(tags)) in self._opened

    def _resolve(
        self,
        service_type: object,
        scope_tags: frozenset,
        data: dict,
    ) -> object:
        """Core resolution.

        1. Check guarded entries for (service_type, scope_tags). If any exist,
           evaluate predicates with **data. At least one must fully match.
        2. If no guarded entries, fast dict lookup in _bindings/_factories.
        3. Subset fallback: try smaller scope tag sets with same logic.
        """
        result = self._resolve_at(service_type, scope_tags, data)
        if result is not _MISS:
            return result

        # Subset fallback on scope tags
        if len(scope_tags) > 1:
            tags_list = sorted(scope_tags, key=id)
            for size in range(len(scope_tags) - 1, 0, -1):
                for subset in _subsets_of_size(tags_list, size):
                    result = self._resolve_at(service_type, frozenset(subset), data)
                    if result is not _MISS:
                        return result

        # Empty scope fallback
        if scope_tags:
            result = self._resolve_at(service_type, frozenset(), data)
            if result is not _MISS:
                return result

        # Nothing found
        tag_names = ", ".join(_name(t) for t in scope_tags)
        data_str = ", ".join(f"{k}={v!r}" for k, v in data.items())
        parts = [_name(service_type)]
        if tag_names:
            parts.append(f"[{tag_names}]")
        if data_str:
            parts.append(f"({data_str})")
        msg = f"No binding for: {''.join(parts)}"
        raise LookupError(msg)

    def _resolve_at(
        self,
        service_type: object,
        scope_tags: frozenset,
        data: dict,
    ) -> object:
        """Resolve at exact scope level. Returns _MISS if nothing found.

        If guarded entries exist for this (service_type) with matching scope,
        predicates are evaluated. At least one must match or _MISS is returned
        (no fallback to non-predicate bindings at this scope level).
        """
        # Check guarded entries only when caller provides data
        guarded = self._guarded.get(service_type) if data else None
        if guarded:
            candidates = [
                (i, etags, preds, val, fac)
                for i, (etags, preds, val, fac) in enumerate(guarded)
                if etags == scope_tags
            ]
            if candidates:
                # Guarded entries exist at this scope — predicates must decide
                for i, etags, preds, val, fac in candidates:
                    if all(pred(**data) for pred in preds.values()):
                        if fac is not None:
                            val = fac()
                            guarded[i] = (etags, preds, val, None)
                        return val
                # Guarded entries exist but none matched — strict failure
                return _MISS

        # No guarded entries at this scope — fast path
        key = (service_type, scope_tags)

        if key in self._bindings:
            return self._bindings[key]

        if key in self._factories:
            value = self._factories.pop(key)()
            self._bindings[key] = value
            self._opened.add(key)
            return value

        return _MISS

    def __getitem__(self, tags: object) -> object:
        """Resolve by service type + scope tags.

        Sugar for get() with no predicate data.

        Usage:
            ctx[Storage]                # service type only
            ctx[Storage, OrderShape]    # service type + scope
            ctx["error"]                # string service type
        """
        if isinstance(tags, tuple):
            if not tags:
                msg = "Empty tag tuple"
                raise ValueError(msg)
            return self._resolve(tags[0], frozenset(tags[1:]), {})
        return self._resolve(tags, frozenset(), {})

    def __contains__(self, tags: object) -> bool:
        """Check if tags resolve."""
        try:
            if isinstance(tags, tuple):
                if not tags:
                    return False
                self._resolve(tags[0], frozenset(tags[1:]), {})
            else:
                self._resolve(tags, frozenset(), {})
        except LookupError:
            return False
        return True

    def __repr__(self) -> str:
        """String representation."""
        parts = []
        for (stype, stags), _val in self._bindings.items():
            labels = [_name(stype), *(_name(t) for t in stags)]
            parts.append("+".join(labels))
        for stype_stags in self._factories:
            if stype_stags not in self._bindings:
                stype, stags = stype_stags
                labels = [_name(stype), *(_name(t) for t in stags), "lazy"]
                parts.append("+".join(labels))
        for stype, entries in self._guarded.items():
            for etags, preds, _val, _fac in entries:
                labels = [_name(stype), *(_name(t) for t in etags)]
                labels.append("+".join(preds))
                parts.append("+".join(labels))
        return f"Context({', '.join(parts)})"


# Sentinel for "no match found" (distinct from None which is a valid value)
_MISS = object()


def _subsets_of_size(items: list, size: int) -> Generator[tuple, None, None]:
    """Generate all subsets of a given size from items."""
    if size == 0:
        yield ()
        return
    for i in range(len(items)):
        for rest in _subsets_of_size(items[i + 1 :], size - 1):
            yield (items[i], *rest)
