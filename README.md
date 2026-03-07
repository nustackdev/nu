# everybase

Term Programming platform for Python — build distributed, persistent and reactive applications with declarative simplicity.

<img width="1314" height="977" alt="image" src="https://github.com/user-attachments/assets/ceeb7f09-29d8-4198-aa19-7a19db8ae9c7" />

## Structure

```
src/everybase/     unified core package
ext/               extension packages
```

### Core (`src/everybase/`)

| Subpackage | Description | Status |
|---|---|---|
| `core/` | Kernel — Term, Flow, Span, Context, Sentinel | exists |
| `abc/` | Toolbox — types, values, morphisms, capabilities, flows | exists |
| `shape/` | Document topology (shapes, slots, refs) | exists |
| `table/` | Relational topology | todo |
| `graph/` | Graph topology | todo |

### Extensions (`ext/`)

**Adapters:**

| Package | Description |
|---|---|
| `eb-virtuals` | PV adapter — refs over KV storages (RocksDB, memory, text) |
| `eb-dict` | Dict adapter — shapes backed by plain Python dicts |

**Types:**

| Package | Description |
|---|---|
| `eb-datetime` | Datetime types |
| `eb-math` | Math types |
| `eb-fin` | Financial types |
| `eb-path` | Path types |
| `eb-uuid` | UUID types |

**Tools:**

| Package | Description |
|---|---|
| `eb-shape-lens` | Terminal shape viewer |
| `eb-tree-view` | HTML tree explorer |

## Development

```bash
make sync      # install
make test      # test
make format    # lint + format
```

## License

MIT
