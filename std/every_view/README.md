# every-view

Standard view implementations for polymorphic views (PV) over KV storages.

## Views

| View | Description |
|------|-------------|
| `ListView` | List-like sequential access |
| `DictView` | Dict-like key-value access |
| `SetView` | Set-like containment |
| `TupleView` | Immutable sequence |
| `FrozenSetView` | Immutable set |
| `ByteArrayView` | Byte array access |
| `FlatDictView` | Flattened dict structure |
| `LightDictView` | Lightweight dict view |

## Install

```bash
pip install every-view
```

## Usage

```python
from every_view import ListView, DictView, SetView
```

## Dependencies

- `pv` - Polymorphic views library

## Development

Part of [everybase monorepo](https://github.com/everyabc/everybase).

```bash
make test-pkg PKG=std/every_view
```
