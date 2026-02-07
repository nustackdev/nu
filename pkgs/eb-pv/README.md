# eb-pv

Specialized Ref implementations for polymorphic views (PV) over KV storages.

## What's Here

- **refs/** - Ref implementations for PV structures
  - `DictRef`, `ListRef` - Collection refs
  - `IntRef`, `StrRef`, `BoolRef` - Primitive refs
  - Base mixins for capabilities (Gettable, Settable, etc.)
- **slots/** - Slot definitions for shapes

## Install

```bash
pip install eb-pv
```

## Usage

```python
from eb_pv.refs import DictRef, ListRef, StrRef
```

## Dependencies

- `every` - Core protocols
- `everybase` - Base type implementations
- `pv` - Polymorphic views library

## Development

Part of [everybase monorepo](https://github.com/everyabc/everybase).

```bash
make test-pkg PKG=std/eb_pv
```
