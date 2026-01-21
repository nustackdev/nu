# everybase

Base implementation layer for the every ecosystem.

Implements core abstractions from `every` with Python primitives.

## What's Here

- **Type implementations** - Python type wrappers (Int, Str, Dict, etc.)
- **Computation bases** - Arithmetic, comparison, logical operation implementations
- **Ref implementations** - Concrete reference types for Python values

## Install

```bash
pip install everybase
```

## Usage

```python
from everybase.types import IntType, StrType
from everybase.comp import AddOp, MulOp
```

## Dependency

```
every (protocols/contracts)
  └── everybase (base implementations)
        └── std/* (type extensions)
        └── pkgs/* (integrations)
```

## Development

Part of [everybase monorepo](https://github.com/everyabc/everybase).

```bash
make test-pkg PKG=abc/everybase
```
