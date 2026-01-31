# everybase

Term Programming platform for Python — build distributed, persistent and reactive applications with declarative simplicity.

## Packages

| | Package | Description |
|---|---|---|
| **Core** | `everyabc` | Contracts — Term, Flow, Ref, Shape, Slot, Context, Sentinel |
| | `everybase` | Base implementations — types, values, morphisms, capabilities |
| **Models** | `everyshape` | Document model — shapes, items, collections |
| | `everytable` | Relational model — tables, columns, queries |
| **Substrates** | `every-pv` | Persistent + reactive — polymorphic views over KV storages |
| | `every-dict` | Plain nested dicts — no storage, no reactivity |
| **Extensions** | `every-flow` | Flow primitives — Seq, Par, Cond, Loop |
| | `every-flow-ext` | Flow extensions — cancellation, progress |
| | `every-type` | Extended types — Decimal, UUID, datetime, Path |
| | `every-notion` | Notion API integration |

## Architecture

```
everyabc
  └── everybase
        ├── everyshape ── every-pv, every-dict
        └── everytable ── every-notion
```

## Development

```bash
make sync      # install
make test      # test
make format    # lint + format
```

## License

MIT
