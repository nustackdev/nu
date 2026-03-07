# eb-pv

PV adapter for everybase — persistent, observable storage over KV backends.

## What's Here

- **refs/** — Ref implementations for PV structures (IntRef, StrRef, DictRef, ListRef, ShapeRef, etc.)
- **views/** — View implementations (DictView, ListView, SetView, TupleView, etc.)
- **adapters/** — Storage backends (RocksDB, InMemory, Text), codecs (JSON, MsgPack, Pickle, Passthrough), observers
- **spans.py** — Atomic and Snapshot span boundaries
- **meta/** — auto_atomic tree transform

## Usage

```python
import eb_pv as pv
from everybase.shape import Shape

class AppState(Shape):
    name = pv.StrRef.slot()
    age = pv.IntRef.slot()
    scores = pv.ListRef.slot(item_type=float)
```

## Dependencies

- `everybase` — core + topologies
- `virtuals-py` — polymorphic views library (in-house, editable)
- `rdbpython` — RocksDB bindings (PyPI, optional)

## Development

Part of [everybase](https://github.com/everyabc/everybase).
