# Storage Layer 1 — Filtering System

Filters are **composable, hashable predicates** for key matching.

They are used by both scan operations (storage layer) and observer subscriptions.

## Design Principles

- Filters are **immutable** and **hashable** (usable in sets/dicts)
- Filters are **composable** via `&` (and) and `|` (or) operators
- Filters are **short-circuit evaluated** for efficiency
- Filters are **declarative** — they describe what to match, not how

## Built-in Filter Types

### PrefixFilter

Match keys starting with a prefix.

```python
f = PrefixFilter(prefix=("users",))
f.matches(("users", "alice"))          # True
f.matches(("users", "alice", "data"))  # True
f.matches(("posts",))                  # False
```

### SuffixFilter

Match keys ending with a suffix.

```python
f = SuffixFilter(suffix=("profile",))
f.matches(("users", "alice", "profile"))  # True
f.matches(("posts", "123", "profile"))    # True
f.matches(("users", "alice"))             # False
```

### LengthFilter

Match keys with exact length.

```python
f = LengthFilter(length=3)
f.matches(("a", "b", "c"))     # True
f.matches(("a", "b"))          # False
f.matches(("a", "b", "c", "d")) # False
```

### WildcardFilter

Match keys with wildcard patterns. `WILDCARD` matches any single segment.

```python
f = WildcardFilter(pattern=("users", WILDCARD, "profile"))
f.matches(("users", "alice", "profile"))  # True
f.matches(("users", "bob", "profile"))    # True
f.matches(("users", "alice", "settings")) # False
```

### PassAll / PassNone

Identity elements for composition.

```python
PassAll().matches(any_key)   # Always True
PassNone().matches(any_key)  # Always False
```

## Composition

Filters compose with `&` (all must match) and `|` (any must match).

```python
# Match users with exactly 3 segments
f = PrefixFilter(prefix=("users",)) & LengthFilter(length=3)
f.matches(("users", "alice", "profile"))  # True
f.matches(("users", "alice"))             # False

# Match users or posts
f = PrefixFilter(prefix=("users",)) | PrefixFilter(prefix=("posts",))
f.matches(("users", "alice"))  # True
f.matches(("posts", "123"))    # True
f.matches(("comments",))       # False
```

Nested compositions are automatically flattened:

```python
(a & b) & c  # becomes And(a, b, c)
(a | b) | c  # becomes Or(a, b, c)
```

## Two Usage Contexts

### Scan Filters (Storage Layer)

`StorageScanOptions` has **two** filter parameters:

```python
StorageScanOptions(
    filter=...,        # Skip keys that don't match
    break_filter=...,  # Stop iteration when key doesn't match
)
```

- `filter`: Continue scanning, but skip non-matching keys
- `break_filter`: Stop the scan entirely when a key doesn't match

Common pattern for subtree operations:

```python
prefix = PrefixFilter(prefix=path)
opts = StorageScanOptions(
    start=path,
    break_filter=prefix,              # Stop when leaving subtree
    filter=prefix & LengthFilter(...) # Include only matching keys
)
```

### Subscription Filters (Observer Layer)

`SubscriptionOptions` has a single filter:

```python
SubscriptionOptions(filter=...)  # Notify when key matches
```

Subscriptions trigger notifications when a modified key matches the filter.

## Custom Filters

Extend `Filter` to create custom filter types:

```python
@dataclass(frozen=True, slots=True)
class RegexFilter(Filter):
    pattern: str

    def matches(self, key: key.Key) -> bool:
        import re
        key_str = "/".join(key)
        return bool(re.match(self.pattern, key_str))

    def __hash__(self) -> int:
        return hash(("regex", self.pattern))

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, RegexFilter):
            return NotImplemented
        return self.pattern == other.pattern
```

Custom filters work with both scan and subscription systems.

**Performance note:** Custom filters cannot be indexed by the subscription registry. They are checked against every key change. For high-frequency notifications with many subscriptions, prefer built-in filter types.

## Registry Indexing

The subscription registry uses hash-based indexing for O(key_length) matching instead of O(n) iteration over all subscriptions.

### How Indexing Works

Built-in filters are indexed by their characteristics:

| Filter Type | Index Key |
|-------------|-----------|
| PrefixFilter | prefix tuple |
| SuffixFilter | suffix tuple |
| LengthFilter | length integer |
| WildcardFilter | (length, signature) |

When a key changes, the registry performs targeted hash lookups instead of checking every subscription.

### Composite Filter Indexing

- `And(A, B, ...)`: Indexed by first filter only. All filters must match, so if the first doesn't match, the whole And fails.

- `Or(A, B, ...)`: Indexed by all constituent filters. Any filter could match, so all must be indexed.

### Custom Filter Indexing

Custom filters cannot be indexed — the registry doesn't know their structure. They are stored in an unindexed set and checked on every key change.

For subscriptions with many custom filters, matching degrades to O(custom_count).

## Choosing Filter Types

| Use Case | Recommended Filter |
|----------|-------------------|
| Subtree operations | PrefixFilter |
| Direct children only | PrefixFilter & LengthFilter |
| Pattern matching | WildcardFilter |
| File extensions | SuffixFilter |
| Complex logic | Composition with & and \| |
| Unusual patterns | Custom filter (with performance caveat) |

---

Filters exist to be **declarative, composable, and efficient**.

Complex matching logic should compose simple filters, not create monolithic custom implementations.
