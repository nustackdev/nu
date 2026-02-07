# everybase

Term Programming platform for Python — build distributed, persistent and reactive applications with declarative simplicity.

## Structure

```
everybase/         core — contracts + base implementations
substrates/        integration substrates by modeling topology
pkgs/              utility + extension packages
```

### Substrates (`substrates/`)

| Package | Topology | Status |
|---|---|---|
| `everyshape` | hierarchical, in-house | exists |
| `everyservice` | flat RPC | wip |
| `everytable` | relational | todo |
| `everyrest` | hierarchical, HTTP | todo |
| `everystream` | push-based events | todo |
| `every-gql` | schema graph | todo |

### Packages (`pkgs/`)

| Package | Description |
|---|---|
| `every-pv` | Polymorphic views over KV storages |
| `every-dict` | Plain nested dicts |
| `every-flow` | Flow primitives — Seq, Par, Cond, Loop |
| `every-flow-ext` | Flow extensions |
| `every-datetime` | Datetime types |
| `every-math` | Math types |
| `every-fin` | Financial types |
| `every-path` | Path types |
| `every-uuid` | UUID types |
| `every-notion` | Notion API integration |

## Development

```bash
make sync      # install
make test      # test
make format    # lint + format
```

## License

MIT
