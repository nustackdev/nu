# abc/every - Design Document

## Vision

**abc/every** is the foundational layer for topology programming. It defines the atoms from which all computation is composed. The design principles are:

1. **Minimal** - Only essential abstractions, nothing more
2. **Composable** - Everything composes cleanly
3. **Substrate-agnostic** - Same tree runs on any backend
4. **Pure structure** - Trees are data, execution is separate

---

## Core Insight

**The tree IS the program. The substrate IS the runtime.**

```
Program = Tree of Units
Runtime = Resource resolution + Tree walk
```

---

## Architecture

```
abc/every/
├── core/               # Foundational atoms
│   ├── unit.py         # Unit base class
│   ├── term.py         # Term (expression unit)
│   └── flow.py         # Flow (orchestration unit)
│
├── resource/           # Resource system
│   ├── resource.py     # Resource base class
│   ├── substrate.py    # Substrate (external systems)
│   └── service.py      # Service (execution infrastructure)
│
├── execution/          # Execution engine
│   ├── context.py      # Context type + helpers
│   ├── executor.py     # Tree walker + resource resolution
│   └── resolution.py   # Smart resolution algorithms
│
├── tree/               # Tree operations
│   ├── path.py         # Path addressing
│   ├── query.py        # Node queries
│   ├── analyze.py      # Tree analysis
│   └── transform.py    # Tree transformations
│
├── term/               # Term implementations (existing)
│   ├── ref.py          # Ref (location)
│   ├── morphism.py     # Morphism (transformation)
│   └── shape.py        # Shape/Slot system
│
└── __init__.py         # Public API
```

---

## Vocabulary (Canonical)

### Atoms

| Term | Definition | Module |
|------|------------|--------|
| **Unit** | Node in execution tree. Base for all computation. | `core/unit.py` |
| **Term** | Unit that returns a value. Expression. Children are Terms only. | `core/term.py` |
| **Flow** | Unit that orchestrates. Children are any Units. | `core/flow.py` |
| **Resource** | Handle with lifecycle (open/close). | `resource/resource.py` |
| **Substrate** | External system factory. Where data lives. | `resource/substrate.py` |
| **Service** | Infrastructure factory. Execution capabilities. | `resource/service.py` |

### Execution

| Term | Definition | Module |
|------|------------|--------|
| **Context** | `dict[ResourceType, Resource]` - available resources | `execution/context.py` |
| **ResourceType** | `type[Substrate] \| type[Service]` - key in context | `execution/context.py` |
| **execute()** | Run unit with context, handle resolution | `execution/executor.py` |
| **provides** | Resources a unit creates for descendants | Unit method |
| **needs** | Resources a unit requires | Unit method |

### Tree

| Term | Definition | Module |
|------|------------|--------|
| **Path** | Address of node: `/0/1/2` | `tree/path.py` |
| **children** | Child units of a node | Unit method |
| **Subtree** | Node and all descendants | concept |

### Resolution

| Term | Definition |
|------|------------|
| **Smart resolution** | (Terms) Analyze subtree, share same-substrate, children-first for different |
| **Explicit scope** | (Flows) User declares provides via Atomic, WithResource, etc. |

---

## Design Rules

### Rule 1: Unit Composition

```
Term.children() -> list[Term]     # Expressions compose with expressions
Flow.children() -> list[Unit]     # Orchestration controls anything
```

### Rule 2: Resource Flow

```
provides flows DOWN (parent to children)
needs looks UP (child finds in ancestors or creates)
```

### Rule 3: Resolution

```
Terms: Smart resolution
  - Analyze subtree needs
  - Same substrate in parent+child → share
  - Different substrates → children first

Flows: Explicit scope
  - provides() declares what to open
  - Default: pass through parent context
```

### Rule 4: Purity

```
Term.is_pure = True  → Operation (no side effects)
Term.is_pure = False → Command (has side effects)
```

---

## Module Specifications

### core/unit.py

```python
class Unit(ABC):
    """Base for all execution tree nodes."""

    def provides(self) -> list[ResourceType]:
        """Resources I create for descendants."""
        return []

    def needs(self) -> list[ResourceType]:
        """Resources I require."""
        return []

    def children(self) -> list[Unit]:
        """My child units."""
        return []

    @abstractmethod
    def run(self, ctx: Context) -> Any:
        """Execute with context."""
        ...
```

### core/term.py

```python
class Term[T](Unit, ABC):
    """Expression unit - computes and returns value."""

    def children(self) -> list[Term]:  # Note: Term, not Unit
        """Child terms (operands)."""
        return []

    @property
    @abstractmethod
    def is_pure(self) -> bool:
        """Whether this term has side effects."""
        ...

    @abstractmethod
    def run(self, ctx: Context) -> T:
        """Compute and return value."""
        ...
```

### core/flow.py

```python
class Flow(Unit, ABC):
    """Orchestration unit - controls execution."""

    _is_flow: ClassVar[bool] = True  # Marker for executor

    def children(self) -> list[Unit]:  # Note: Unit, not Term
        """Child units to orchestrate."""
        return []

    @abstractmethod
    def run(self, ctx: Context) -> Any:
        """Execute orchestration logic."""
        ...
```

### resource/resource.py

```python
class Resource(ABC):
    """Handle with lifecycle."""

    @abstractmethod
    def release(self) -> None:
        """Release resource on scope exit."""
        ...
```

### resource/substrate.py

```python
class Substrate(ABC):
    """External system that creates resources."""

    @abstractmethod
    def create(self) -> Resource:
        """Create new resource handle."""
        ...
```

### resource/service.py

```python
class Service(ABC):
    """Execution infrastructure that creates resources."""

    @abstractmethod
    def create(self) -> Resource:
        """Create new service resource."""
        ...
```

### execution/context.py

```python
# Type aliases
ResourceType = type[Substrate] | type[Service]
Context = dict[ResourceType, Resource]

# Helper functions
def get_resource[R: Resource](ctx: Context, resource_type: type[R]) -> R:
    """Get typed resource from context."""
    ...
```

### execution/executor.py

```python
# Registry
_providers: dict[ResourceType, Substrate | Service] = {}

def register(provider: Substrate | Service) -> None:
    """Register resource provider."""
    ...

def execute(unit: Unit, ctx: Context | None = None) -> Any:
    """Execute unit with smart resolution."""
    ...
```

---

## Implementation Plan

### Phase 1: Core Atoms
1. `core/unit.py` - Unit base class
2. `core/term.py` - Term class (extends Unit)
3. `core/flow.py` - Flow class (extends Unit)

### Phase 2: Resource System
4. `resource/resource.py` - Resource base
5. `resource/substrate.py` - Substrate base
6. `resource/service.py` - Service base

### Phase 3: Execution
7. `execution/context.py` - Context types + helpers
8. `execution/resolution.py` - Resolution algorithms
9. `execution/executor.py` - Main executor

### Phase 4: Tree Tools
10. `tree/path.py` - Path addressing
11. `tree/query.py` - Node queries
12. `tree/analyze.py` - Tree analysis
13. `tree/transform.py` - Tree transforms

### Phase 5: Integration
14. Update existing `term/` modules
15. Update `__init__.py` exports
16. Write tests
17. Documentation

---

## Quality Checklist

- [ ] All classes have docstrings
- [ ] All methods have type hints
- [ ] All public API documented
- [ ] No circular imports
- [ ] Clean separation of concerns
- [ ] Minimal dependencies between modules
- [ ] Tests pass
- [ ] Examples work

---

## Files to Create/Update

### Create New
- `abc/every/src/every/core/__init__.py`
- `abc/every/src/every/core/unit.py`
- `abc/every/src/every/core/term.py`
- `abc/every/src/every/core/flow.py`
- `abc/every/src/every/resource/__init__.py`
- `abc/every/src/every/resource/resource.py`
- `abc/every/src/every/resource/substrate.py`
- `abc/every/src/every/resource/service.py`
- `abc/every/src/every/execution/__init__.py`
- `abc/every/src/every/execution/context.py`
- `abc/every/src/every/execution/resolution.py`
- `abc/every/src/every/execution/executor.py`
- `abc/every/src/every/tree/__init__.py`
- `abc/every/src/every/tree/path.py`
- `abc/every/src/every/tree/query.py`
- `abc/every/src/every/tree/analyze.py`

### Update Existing
- `abc/every/src/every/term/term.py` - Integrate with Unit
- `abc/every/src/every/term/ref.py` - Add needs()
- `abc/every/src/every/term/morphism.py` - Add children() properly
- `abc/every/src/every/__init__.py` - Export new API
