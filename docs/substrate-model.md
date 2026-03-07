# Substrate Model

How topology manifests in code. How one algebra covers every backend.

## Ref Types Are Topology

A Ref type doesn't just "point to data." It encodes the **topological relationship** between units of information.

```
ShapesMappingRef    one-to-many:    Market has many Symbols
ShapeRef            one-to-one:     Market has one LastOrder
ItemRef             attribute:      Symbol has a price
SequenceRef         ordered-many:   Market has ordered Prices
```

Each substrate introduces Ref types that express its native topology:

| Substrate | Ref types | Topology expressed |
|---|---|---|
| everybase.shape | ItemRef, ShapeRef, ShapesMappingRef | Hierarchical containment |
| eb_rest | ResourceRef, ShapesDictRef | HTTP resource hierarchy |
| eb_service | (none — flat) | Flat method dispatch |
| everytable (future) | ForeignKeyRef, JoinRef | Relational references |

The Ref IS the topology. Not metadata about it. Not a label. The actual structural relationship between data.

## Topology Determines the Substrate

The substrate taxonomy classifies integration paradigms by their **modeling topology** — how resources are addressed and what operations exist.

```
Topology                 Substrate       Atomic unit      Refs?
──────────────────       ─────────       ───────────      ─────
Hierarchical, in-house   everybase.shape        item             yes — parent chains, item-level CRUD
Hierarchical, HTTP       eb_rest         resource         yes — parent chains, resource-level CRUD
Flat (RPC)               eb_service      method call      no — no persistent addressing
Relational               everytable        row              yes — foreign keys, joins
Push-based               everystream       event            TBD
Schema graph             eb_gql          query            TBD
```

Flat topology (eb_service) has no Refs because there's nothing to persistently address. Each method call is a one-shot morphism. This isn't a missing feature — it's the correct modeling for flat dispatch.

## The Four Layers

Every substrate follows the same layered architecture:

```
Layer       What it provides                    Example (everybase.shape)
─────       ────────────────                    ──────────────────
1. core     Term, Ref, Value, Morphism,         everybase
            Context, Model

2. model    Ref types, morphisms,               everybase.shape
            capabilities for the topology       (ItemRef, ItemGetOp, ShapesMappingRef)

3. adapter  Concrete storage wiring             eb_virtuals (KV views)
            (resolve → location, fetch → data)  eb_dict (plain dicts)

4. app      Domain-specific definitions         weather station, trading app
```

Each layer answers a different question:

- **Core**: what CAN exist in a computation?
- **Model**: what TOPOLOGICAL PATTERNS does this paradigm have?
- **Adapter**: WHERE does data physically live?
- **App**: WHAT specific data exists in this domain?

### How This Plays Out Per Substrate

**everybase.shape** (hierarchical, in-house):
```
core     → everybase (Term, Ref, Context)
model    → everybase.shape (ItemRef, ShapesMappingRef, ItemGetOp, Shape)
adapter  → eb_virtuals (KV views, transactions) | eb_dict (plain dicts)
app      → Market(Shape), WeatherStation(Shape), etc.
```

**eb_rest** (hierarchical, HTTP):
```
core     → everybase
model    → eb_rest (ResourceRef, ShapesDictRef, ResourceGetOp, Service)
adapter  → (none — HTTP baked in, one backend)
app      → GitHubService, StripeService, etc.
```

**eb_service** (flat RPC):
```
core     → everybase
model    → eb_service (Interface, ServiceMethodCall)
adapter  → (none — service client baked in)
app      → SolanaRpc, gRPC services, etc.
```

**everytable** (relational, future):
```
core     → everybase
model    → everytable (ForeignKeyRef, JoinRef, QueryMorphism, Table)
adapter  → eb_postgres, eb_sqlite, eb_notion, etc.
app      → UserTable, OrderTable, etc.
```

Note: eb_rest and eb_service have no adapter layer. REST always uses HTTP. RPC always uses the service client. There's no alternative backend — the transport IS the substrate. In contrast, everybase.shape and everytable are storage-agnostic models with pluggable adapters.

## One Algebra, Every Backend

The same expression tree can span multiple substrates:

```python
# Read from REST API, store in local KV, query from database
await Seq(
    LocalCache.repo.set(
        GitHub.repos["octocat/hello"].get()    # eb_rest → HTTP
    ),                                          # everybase.shape → PV storage
    Analytics.downloads.set(
        DB.repos.where(name="hello").count()    # everytable → SQL
    ),                                          # everybase.shape → PV storage
).execute(ctx)
```

This works because every substrate produces Terms. Terms compose. Context resolves the right backend for each Shape. The algebra doesn't care what's behind the Ref.

## The Collection Ref Pattern

Collection refs deserve special attention — they express the **one-to-many relationship** that appears across every topology:

```python
# everybase.shape: dict of shapes
Market.symbols["AAPL"]              # ShapesMappingRef → ShapeRef

# eb_rest: collection of resources
GitHub.repos["octocat/hello"]       # ShapesDictRef → ResourceRef

# everytable (future): foreign key relation
Order.items[42]                     # ForeignKeyRef → RowRef
```

Same `collection["key"] → typed ref` pattern. Same `__getitem__`. Different topology, same algebra. Whether the data is in a local dict, an HTTP endpoint, or a database row — the structural relationship is expressed identically.

This is topology as type. The Ref type declares the relationship. The substrate implements the resolution. The algebra composes it all.
