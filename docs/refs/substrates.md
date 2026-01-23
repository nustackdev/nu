# Substrates

A substrate defines WHERE values live and HOW to access them.

## Substrate Components

Each substrate provides:

| Component | Purpose |
|-----------|---------|
| **RefBase** | Storage implementation (fetch, resolve) |
| **Context** | Execution environment (storage handle, transaction) |
| **Concrete Refs** | RefBase + TypeBases combined |

## Implementing a Substrate

### Step 1: Define the RefBase

```python
class MySubstrateRef[T](Ref[T], ABC):
    """Base for all refs in MySubstrate."""

    def __init__(self, ...substrate_specific_args...):
        # Store substrate-specific state
        ...

    def resolve(self, ctx: Context) -> Location:
        # Return identity/location representation
        ...

    @abstractmethod
    def fetch(self, ctx: Context) -> T | Sentinel:
        # Subclasses implement based on value vs container
        ...
```

### Step 2: Define Context Requirements

```python
@attrs.frozen
class MySubstrateContext:
    """Context for MySubstrate execution."""
    connection: SomeConnection
    transaction: SomeTransaction | None = None
```

### Step 3: Create Concrete Refs

```python
class MyIntRef(MySubstrateRef[int], IntRefBase):
    """Integer ref for MySubstrate."""

    def fetch(self, ctx: Context) -> int | Sentinel:
        # Fetch integer from substrate
        ...

    def _wrap(self, op: Term) -> IntRef:
        # Operations return Python memory refs
        from everybase.py import IntRef
        return IntRef(op)
```

## Existing Substrates

### Python Memory (`everybase/py/`)

The simplest substrate - values live in Python runtime memory.

```python
class PyRef[T](Ref[T]):
    _source: T | Term[T]

    def fetch(self, ctx: Context) -> T | Sentinel:
        if isinstance(self._source, Term):
            return self._source.execute(ctx)
        return self._source
```

**Context:** Empty (values already accessible)

**Use case:** Literal values, expression results, in-memory computation

### PV Storage (`every_pv/`)

Values live in a view hierarchy backed by key-value storage.

```python
class PVRefBase[T](Ref[T], ABC):
    _address: PathAddress
    _parent: PVRefBase | None
    _shape: type[Shape] | None

    def resolve(self, ctx: Context) -> Path:
        # Build path tuple from parent chain
        ...
```

**Context:** root_view (storage file handle + transaction state)

**Use case:** Persistent data, typed collections, hierarchical structures

**Ref types:**
- `PVPrimitiveRef[T]` - leaf values (int, str, etc.)
- `PVViewRef[T, ViewT]` - containers (DictView, ListView, etc.)

## Substrate Design Principles

### 1. Refs Point, Operations Compute

Substrate refs point to locations. When used in operations, results become Python memory refs:

```python
pv_price = PVIntRef(address="price", ...)  # Points to PV storage
result = pv_price + 100                     # IntRef(AddOp(...)) - Py memory
```

This is intentional: the operation result is a computation, not a storage location.

### 2. Context Carries Environment

Each substrate defines what context it needs:

| Substrate | Context Contains |
|-----------|------------------|
| Python | Nothing (empty) |
| PV | root_view, transaction |
| Notion | HTTP client, auth |
| Postgres | connection, cursor |

### 3. Resolve for Identity, Fetch for Value

- `resolve(ctx)` returns a substrate-specific location identifier
- `fetch(ctx)` actually retrieves the value

Some substrates may have trivial resolve (Python), others build complex paths (PV).

## Future Substrates

Planned or potential substrates:

| Substrate | Package | Description |
|-----------|---------|-------------|
| Notion | `every_notion/` | Notion API pages/databases |
| Postgres | `every_pg/` | PostgreSQL rows/columns |
| Redis | `every_redis/` | Redis keys/values |
| HTTP/REST | `every_http/` | REST API endpoints |
| SQLite | `every_sqlite/` | SQLite tables |
