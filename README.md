# everybase

Term Programming platform for Python — build distributed, persistent and reactive applications with declarative simplicity.

<img width="1314" height="977" alt="image" src="https://github.com/user-attachments/assets/ceeb7f09-29d8-4198-aa19-7a19db8ae9c7" />

## Structure

```
core/              core libraries
pkgs/              optional extension packages
```

### Core (`core/`)

| Package | Description | Status |
|---|---|---|
| `everybase` | Contracts + base implementations | exists |
| `everyshape` | Declarative document model (shapes, slots, refs) | exists |
| `everypv` | Polymorphic views over KV storages | exists |
| `everytable` | Relational data model | todo |
| `everystream` | Push-based event streams | todo |
| `everygraph` | Graph data model | todo |

### Packages (`pkgs/`)

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
