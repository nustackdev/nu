# everybase

Term Programming platform for Python — build distributed, persistent and reactive applications with declarative simplicity.

<img width="1314" height="977" alt="image" src="https://github.com/user-attachments/assets/ceeb7f09-29d8-4198-aa19-7a19db8ae9c7" />

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
| `eb_table` | relational | todo |
| `eb_stream` | push-based events | todo |

### Packages (`pkgs/`)

| Package | Description |
|---|---|
| `eb-pv` | Polymorphic views over KV storages |
| `eb-flow` | Flow primitives — Seq, Par, Cond, Loop |
| `eb-flow-ext` | Flow extensions |
| `eb-datetime` | Datetime types |
| `eb-math` | Math types |
| `eb-fin` | Financial types |
| `eb-path` | Path types |
| `eb-uuid` | UUID types |

## Development

```bash
make sync      # install
make test      # test
make format    # lint + format
```

## License

MIT
