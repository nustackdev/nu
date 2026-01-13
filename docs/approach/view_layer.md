# View Layer — Philosophy

The view layer adds **data structure semantics** to hierarchical containers.

It interprets containers as familiar Python collections (dict, list, set) while delegating all storage operations to the Container API.

## Core Design

### Thin Wrappers, No State

Views are stateless. They hold no data — only a reference to a Container and a Registry.

```python
@attrs.frozen
class ViewBase:
    container: Container  # Delegates storage ops
    registry: ViewRegistry  # Handles nested type mapping
```

Every read goes to storage. Every write goes to storage. Views are lenses, not caches.

### Protocol-Based Capabilities

Views define their own interfaces. No mandatory base protocol.

A view implements what makes sense for its semantics:

| View | Key Protocols |
| ------ | -------------- |
| `DictView` | `Subscriptable`, `Assignable`, `Containable`, `Convertible` |
| `ListView` | `Subscriptable`, `Appendable`, `Insertable`, `Poppable` |
| `SetView` | `Addable`, `Removable`, `Containable` |
| `QueueView` | `Appendable`, `Poppable` |

Capability protocols are runtime-checkable:

```python
if isinstance(view, Convertible):
    data = view.extract()

if isinstance(view, Nestable):
    child = view.open_child("users", DictView)
```

No inheritance hierarchy. Just composition.

### View Identity

Each view has two class-level attributes:

```python
class DictView(ViewBase):
    STRUCTURE = ContainerStructure(1)  # Storage marker
    PROTOCOL = ContainerProtocol.MAPPING | ContainerProtocol.MUTABLE
    CONTAINER_CLS = dict  # Python type association
```

**STRUCTURE** — unique ID stored with container data. Used to recreate the correct view when reading.

**PROTOCOL** — optional bitflags for debugging/visualization. Not enforced.

**CONTAINER_CLS** — Python type this view represents. Enables automatic nested handling.

## Registry: Type Resolution

Registry solves bidirectional mapping:

| Direction | Lookup | Purpose |
| ----------- | -------- | --------- |
| Writing | `dict` → `DictView` | Store Python value |
| Reading | `structure=1` → `DictView` | Extract stored data |

```python
registry = ViewRegistry()
registry.register(DictView)   # structure=1, type=dict
registry.register(ListView)   # structure=2, type=list

# Writing: Python type → View
view_class = registry.get_view_for_type(dict)

# Reading: Structure ID → View
view_class = registry.get_view_for_structure(1)
```

Registry enables recursive handling. A DictView storing a list automatically creates a ListView for the nested data.

## Address Normalization

Views translate user-facing addresses to storage keys.

```python
# ListView: negative indices → positive
tasks[-1]  # becomes tasks[len(tasks) - 1]

# DictView: passthrough
users["alice"]  # stays "alice"
```

The `normalize_address` hook centralizes this translation:

```python
class ListView(ViewBase):
    def normalize_address(self, address: int) -> int:
        if address < 0:
            return len(self) + address
        return address
```

Views own address semantics. Container sees only normalized keys.

## Population and Extraction

Views handle bidirectional conversion between Python values and storage.

**Population** (Python → Storage):

```python
users["alice"] = {
    "name": "Alice",
    "tags": ["python", "rust"]
}
# Registry: dict → DictView, list → ListView
# Creates nested containers automatically
```

**Extraction** (Storage → Python):

```python
data = users.extract()
# Returns: {"alice": {"name": "Alice", "tags": ["python", "rust"]}}
# Registry reconstructs correct types from structure IDs
```

Two capability protocols:

- `Initializable` — can store Python values (`store()`)
- `Convertible` — can extract to Python values (`extract()`)

## Length Tracking

Two strategies for `__len__`:

**Metadata-based** — stored in container metadata, O(1) access:

```python
class MetadataBasedChildrenCountBase:
    def __len__(self) -> int:
        return self.container.get_metadata("__len__", default=0)

    def _increment_length(self):
        # Called after add operations
```

**Live counting** — iterates children, always accurate:

```python
class LiveChildrenCountBase:
    def __len__(self) -> int:
        return sum(1 for _ in self.container.iter_child_keys())
```

Choose based on access pattern. Frequent length checks → metadata. Rare checks → live.

## Navigation

Views support traversal:

```python
# Open root view
users = DictView.open_root(ctx)

# Navigate to child
alice = users.open_child("alice", DictView)

# Navigate to parent
parent = alice.open_parent()

# Open at path
view = DictView.open_at(
    (("users", DictView), ("alice", DictView)),
    "profile",
    ctx
)
```

Navigation preserves registry context. Child views use parent's registry.

## Naming Conventions

### Nouns

| Term | Meaning |
| ------ | --------- |
| `view` | The lense through which container is accessed |
| `address` | User-facing location (may be `-1`, `"alice"`, etc.) |
| `path` | Sequence of typed navigation segments |
| `structure` | Storage marker identifying view type |

### Words to Avoid

- ~~key~~ → use `address` (key is storage/container layer)
- ~~site~~ → use `path` (site is container layer)
- ~~type~~ → use `structure` when referring to storage identity

## Context Handling

Views require explicit storage context:

```python
# Read-only snapshot
with storage.snapshot() as snap:
    users = DictView.open_root(snap)
    data = users.extract()

# Read-write transaction
with storage.transaction() as tx:
    users = DictView.open_root(tx)
    users["alice"] = {"name": "Alice"}
```

No implicit transactions. No global state.

## What View Does NOT Do

### No Storage Operations

View doesn't handle:

- KV storage access
- Encoding/decoding
- Transaction management
- Byte-level operations

These are Storage Layer 1 responsibilities.

### No Hierarchy Enforcement

View doesn't handle:

- Parent validation
- Container creation rules
- Type consistency across tree

These are Container Layer 2 responsibilities.

### No Business Logic

View doesn't handle:

- Domain validation
- Business rules
- Application constraints
- Schema enforcement

These are Shape Layer 4 responsibilities.

### No Caching

View doesn't:

- Cache reads
- Buffer writes
- Maintain dirty state
- Track changes internally

Every operation hits storage. Views are passthrough.

---

Familiar interface, explicit delegation, type-aware nesting.
