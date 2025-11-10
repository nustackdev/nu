# Layer 3: View

## What It Is

View adds data structure semantics on top of Tree's containers. It makes containers behave like Python data structures (dicts, lists, sets) while handling all storage details automatically.

## Key Concepts

### Views as Data Structures

Tree sees containers. Views see data structures:

```python
# Tree Layer 2: generic containers
tree.create_container(("users",))
tree.set_child("alice", value)

# View Layer 3: Python data structures
users["alice"] = {"name": "Alice"}
profile = users["alice"]
```

Each view implements familiar Python protocols:

- **DictView**: dict-like (`__getitem__`, `keys()`, `values()`)
- **ListView**: list-like (`append()`, `pop()`, `[0]`)
- **SetView**: set-like (`add()`, `remove()`, `in`)
- **QueueView**: queue-like (`enqueue()`, `dequeue()`)

Views define their own interface. No mandatory protocols.

### View Identity

Each view has two attributes:

```python
class DictView(View):
    structure = ContainerStructure(1)     # Storage identifier
    protocol = ContainerProtocol.MUTABLE  # Behavior hints
```

**ContainerStructure** (int):

- Unique ID for this view type
- Used to recreate correct view when reading
- Examples: `1` = dict, `2` = list, `3` = set

**ContainerProtocol** (bitflags):

- Optional hints for debugging/visualization
- NOT enforced - just metadata
- Examples: `MUTABLE`, `SIZED`, `INDEXED`

### Registry: Type Mapping

Registry maps between Python types and Views:

```python
# Python type → View (for writing)
registry.register(dict → DictView)
registry.register(list → ListView)
registry.register(set → SetView)

# Structure ID → View (for reading)
registry.register(1 → DictView)
registry.register(2 → ListView)
registry.register(3 → SetView)
```

This enables automatic nested handling:

```python
# Writing
users["alice"] = {"name": "Alice", "tags": ["python"]}
# Registry: dict → DictView, list → ListView

# Reading
data = users["alice"]  # Returns: {"name": "Alice", "tags": ["python"]}
# Registry: structure=1 → DictView, structure=2 → ListView
```

### Auto-Population and Extraction

Views handle nested structures automatically.

**Population** (Python → Storage):

```python
users["alice"] = {
    "name": "Alice",
    "profile": {
        "age": 30,
        "tags": ["python", "rust"]
    }
}
```

Stores as:

```text
("users", "alice") → <CONTAINER: structure=1>
("users", "alice", "name") → "Alice"
("users", "alice", "profile") → <CONTAINER: structure=1>
("users", "alice", "profile", "age") → 30
("users", "alice", "profile", "tags") → <CONTAINER: structure=2>
("users", "alice", "profile", "tags", 0) → "python"
("users", "alice", "profile", "tags", 1) → "rust"
```

**Extraction** (Storage → Python):

```python
data = users.extract()
# Returns: {
#     "alice": {
#         "name": "Alice",
#         "profile": {
#             "age": 30,
#             "tags": ["python", "rust"]
#         }
#     }
# }
```

Views implement population/extraction protocols:

```python
class View:
    def store(self, value, /, *, replace=False):
        """Populate container from Python value."""
        ...

    def extract(self):
        """Extract container to Python value."""
        ...
```

## Operations

### DictView Operations

```python
# Create/access dict view
users # DictView

# Get/set like dict
users["alice"] = {"name": "Alice", "age": 30}
alice = users["alice"]

# Dict methods
keys = users.keys()              # ["alice", "bob"]
values = users.values()          # [{"name": "Alice"}, ...]
items = users.items()            # [("alice", {...}), ...]
has_alice = "alice" in users     # True

# Mutation
users.update({"charlie": {"name": "Charlie"}})
users.pop("alice")
users.clear()

# Extract entire dict
data = users.extract()  # {"alice": {...}, "bob": {...}}
```

### ListView Operations

```python
# Create/access list view
tasks # ListView

# Get/set like list
tasks.append("Task 1")
tasks.append("Task 2")
first = tasks[0]
tasks[1] = "Updated task"

# List methods
tasks.insert(1, "New task")
tasks.remove("Task 1")
last = tasks.pop()

# Iteration
for task in tasks:
    print(task)

# Extract entire list
all_tasks = tasks.extract()  # ["Task 1", "Task 2"]
```

### SetView Operations

```python
# Create/access set view
tags  # SetView

# Set operations
tags.add("python")
tags.add("rust")
has_python = "python" in tags  # True

# Set methods
tags.remove("python")
tags.discard("java")  # Silent if missing

# Set algebra
union = tags.union(other)
intersection = tags.intersection(other)

# Extract entire set
all_tags = tags.extract()  # {"python", "rust"}
```

### QueueView Operations

```python
# Create/access queue view
queue  # QueueView

# Queue operations (FIFO)
queue.enqueue({"type": "login"})
event = queue.dequeue()  # First in, first out
next_event = queue.peek()  # Look without removing

is_empty = queue.is_empty()
size = len(queue)

# Extract as list
events = queue.extract()
```

## How It Uses Layer 2

View operations map to Tree operations:

### DictView: `users["alice"] = {"name": "Alice"}`

```python
# View Layer 3
users["alice"] = {"name": "Alice"}

# ↓ uses Tree Layer 2
tree.create_container(("users", "alice"), structure=1)
tree.set_child_primitive(("users", "alice"), "name", "Alice")

# ↓ uses Storage Layer 1
storage.put(("users", "alice"), <CONTAINER: structure=1>)
storage.put(("users", "alice", "name"), "Alice")
```

### ListView: `tasks.append("Task 1")`

```python
# View Layer 3
tasks.append("Task 1")

# ↓ uses Tree Layer 2
count = tree.count_children(("tasks",))
tree.set_child_primitive(("tasks",), count, "Task 1")

# ↓ uses Storage Layer 1
storage.put(("tasks", 0), "Task 1")
```

## Registry System

### Registering Views

```python
from redwood.view import ViewRegistry
from redwood.view.views import DictView, ListView

registry = ViewRegistry()

# Register built-in views
registry.register_view(
    DictView,
)
# structure_id=1,
# container_type=dict,

registry.register_view(
    ListView,
)
# structure_id=2,
# container_type=list,
```

### Registry Lookup

**Reading:** Structure ID → View

```python
view_class = registry.get_view_for_structure(1)  # Returns: DictView
```

**Writing:** Python Type → View

```python
view_class = registry.get_view_for_container_type(dict)  # Returns: DictView
```

## Context Management

### Context Manager (Recommended)

```python
# Write operations
with DictView().open() as users:
    users["alice"] = {"name": "Alice"}
    # Auto-commits on success, auto-rollback on exception

# Read-only snapshot
with DictView().open(readonly=True) as users:
    users["alice"]
```

### Direct Access [TBD]

```python
# Read without transaction
users = tree.at("users").view(DictView)
count = len(users)

# Write with manual transaction
with tree.transaction() as tx:
    users = tree.at("users").view(DictView, ctx=tx)
    users["alice"] = {"name": "Alice"}
```

## Navigation

### Auto-View Detection

```python
# Store nested structures - types auto-detected
users["alice"] = {
    "name": "Alice",
    "tags": ["python"],
    "permissions": {"read", "write"}
}

# Read back - types preserved
alice = users["alice"]  # dict
tags = alice["tags"]     # list
perms = alice["permissions"]  # set
```

## Custom Views

```python
from redwood.view import View, ContainerStructure, ContainerProtocol

class DocumentView(View):
    """Custom view for documents."""

    structure = ContainerStructure(100)
    protocol = ContainerProtocol.MUTABLE

    def get_title(self):
        return self.container.get_primitive_child("title")

    def set_title(self, title):
        self.container.set_primitive_child("title", title)

    def extract(self):
        return {"title": self.get_title(), ...}

    def store(self, value, /, *, replace=False):
        self.set_title(value["title"])

# Register
registry.register_view(DocumentView,)
```

## What View Does NOT Do

### No Storage Operations

Doesn't handle:

- KV storage access
- Encoding/decoding
- Transaction management

These are Storage Layer 1 responsibilities.

### No Hierarchy Enforcement

Doesn't handle:

- Parent validation
- Container creation rules
- Type consistency

These are Tree Layer 2 responsibilities.

### No Application Logic

Doesn't handle:

- Business rules
- Domain validation
- Command/query patterns

These are Shapes Layer 4 responsibilities.
