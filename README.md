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
| `eb_shape` | hierarchical, in-house | exists |
| `eb_service` | flat RPC | wip |
| `eb_table` | relational | todo |
| `eb_rest` | hierarchical, HTTP | todo |
| `eb_stream` | push-based events | todo |
| `eb-gql` | schema graph | todo |

### Packages (`pkgs/`)

| Package | Description |
|---|---|
| `eb-pv` | Polymorphic views over KV storages |
| `eb-dict` | Plain nested dicts |
| `eb-flow` | Flow primitives — Seq, Par, Cond, Loop |
| `eb-flow-ext` | Flow extensions |
| `eb-datetime` | Datetime types |
| `eb-math` | Math types |
| `eb-fin` | Financial types |
| `eb-path` | Path types |
| `eb-uuid` | UUID types |
| `eb-notion` | Notion API integration |

## Development

```bash
make sync      # install
make test      # test
make format    # lint + format
```

## License

MIT
