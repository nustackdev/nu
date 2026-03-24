# Context

Context carries everything a term needs at runtime - storage connections, navigators, configs. You bind things in, terms look them up during execution.

## How it works

You put things in with `bind()`, take them out with `ctx[...]`.

```python
ctx = Context().bind(my_database, Database)

ctx[Database]  # -> my_database
```

Every binding is addressed by tags. The first tag is always the type - what you're storing. You can add more tags to distinguish between multiple bindings of the same type.

```python
ctx = (Context()
    .bind(user_db, Database, UserShape)
    .bind(order_db, Database, OrderShape)
)

ctx[Database, UserShape]   # -> user_db
ctx[Database, OrderShape]  # -> order_db
```

Tags can be anything hashable - types, strings, ints:

```python
ctx.bind(worker_a, Worker, 0)
ctx.bind("timeout", "error")

ctx[Worker, 0]   # -> worker_a
ctx["error"]     # -> "timeout"
```

## Immutability

`bind()` returns a new Context. The original doesn't change.

```python
ctx_a = Context().bind("x", Storage)
ctx_b = ctx_a.bind("y", Storage)

ctx_a[Storage]  # -> "x"
ctx_b[Storage]  # -> "y"
```

This is what makes spans work - a span creates a child context for its subtree without touching the parent.

## Tag fallback

When there's no exact match, Context tries progressively fewer tags.

```python
ctx = (Context()
    .bind("default_db", Database)
    .bind("market_db", Database, MarketShape)
)

ctx[Database, MarketShape]  # -> "market_db" (exact)
ctx[Database, OrderShape]   # -> "default_db" (no OrderShape match, falls back)
ctx[Database]               # -> "default_db" (exact)
```

More tags = more specific. Fallback always goes toward fewer tags, never drops the type.

## Lazy bindings

Sometimes you don't want to create a resource until it's actually needed. `lazy()` binds a factory that runs on first access and caches the result.

```python
ctx = ctx.lazy(lambda: open_expensive_connection(), Database)

# nothing opened yet
ctx[Database]  # factory runs here, result cached
ctx[Database]  # cached, factory not called again
```

Spans use this for transactions - if a subtree never touches storage, the transaction is never opened.

## Predicates

Regular bindings are static - one tag set, one value. Predicates add dynamic routing: same tags, multiple values, picked by a condition at lookup time.

Use case: sharded storage. You have two databases for the same Shape, split by key range.

### Binding with predicates

Pass callables as kwargs to `bind()`:

```python
ctx = (Context()
    .bind(shard_low, View, Market,
          routing=lambda site, path: site[0] < 16)
    .bind(shard_high, View, Market,
          routing=lambda site, path: site[0] >= 16)
)
```

Each entry has the same tags `(View, Market)` but different predicates. The predicate decides which entry wins.

### Looking up with data

Use `get()` and pass the data predicates need as kwargs:

```python
ctx.get(View, Market, site=(5,), path=some_path)
# -> shard_low (5 < 16, predicate passes)

ctx.get(View, Market, site=(20,), path=some_path)
# -> shard_high (20 >= 16)
```

The kwargs you pass to `get()` are forwarded as `**kwargs` to every predicate. Your predicate's parameter names must match what the caller passes.

### Who calls get()?

The ref base code does. It always passes the same data regardless of whether predicates are bound:

```python
# inside ViewRef.fetch() - this never changes
root_view = ctx.get(View, shape, site=site_tuple, path=view_path)
```

If no predicates are bound, the data is ignored and it behaves like `ctx[View, shape]`. If predicates are bound, they receive the data and route accordingly. The ref doesn't know or care.

### Resolution with predicates

When predicate entries exist for a tag set, they take over. The rules:

- All predicates on an entry must pass (AND). An entry with `routing=...` and `tier=...` only matches if both return truthy.
- At least one entry must match. If none do, it's a `LookupError` - not a silent fallback to a non-predicate binding at the same tags.
- If no predicate entries exist for those tags, predicates aren't involved at all - regular fast lookup.

### Multiple dimensions

Multiple predicates on one entry means AND. For 2 shards x 2 tiers, you need 4 entries:

```python
ctx = (Context()
    .bind(hot_low,  View, Market,
          shard=lambda site, path: site[0] < 16,
          tier=lambda site, path: site[1] == "hot")
    .bind(cold_low, View, Market,
          shard=lambda site, path: site[0] < 16,
          tier=lambda site, path: site[1] == "cold")
    .bind(hot_high, View, Market,
          shard=lambda site, path: site[0] >= 16,
          tier=lambda site, path: site[1] == "hot")
    .bind(cold_high, View, Market,
          shard=lambda site, path: site[0] >= 16,
          tier=lambda site, path: site[1] == "cold")
)
```

### Predicate contract

Each type defines what data the caller passes. If you write predicates for that type, your lambdas must accept those kwargs:

| Type | Caller passes | Used by |
|---|---|---|
| View (eb-virtuals) | `site`, `path` | ViewRef, PrimitiveRef |
| dict (eb-dict) | `site` | RefBase |

## API

```python
# Bind a value
ctx = ctx.bind(value, TypeTag, *more_tags, **predicates)

# Bind a lazy factory (zero-arg callable, cached on first access)
ctx = ctx.lazy(factory, TypeTag, *more_tags, **predicates)

# Look up (no predicate data)
ctx[TypeTag]
ctx[TypeTag, AnotherTag]

# Look up (with predicate data)
ctx.get(TypeTag, AnotherTag, site=..., path=...)

# Check existence
ctx.has(TypeTag, AnotherTag)  # -> bool

# Check if lazy was materialized
ctx.was_opened(TypeTag)  # -> bool
```
