# Core

Foundation packages for everybase. All use the `every*` naming convention.

| Package | Description | Status |
|---|---|---|
| `everybase` | Contracts + base implementations (types, values, morphisms, flows) | exists |
| `everyshape` | Declarative document model (shapes, slots, refs, reactive flows) | exists |
| `everypv` | Polymorphic views over KV storages (refs, views, adapters, spans) | exists |
| `everytable` | Relational data model | stub |
| `everystream` | Push-based event streams | stub |
| `everygraph` | Graph data model | stub |

## Dependencies

```
everybase
├── everyshape
│   └── everypv (+ pv, tkv)
├── everytable
├── everystream
└── everygraph
```
