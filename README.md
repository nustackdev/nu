# Nu

Nu lets you write distributed, reactive, durable, concurrent, adaptive systems as pure interaction composition, and derive the hard properties (atomicity, recoverability, cacheability, scalability) via transformation.

## Getting started

```bash
pip install nu[minimal]
```

With persistent storage:

```bash
pip install nu[default]  # includes virtuals, RocksDB, type extensions
```

Requires Python 3.12+.

## Infra

| Package | What |
|---------|------|
| **[virtuals](https://github.com/nustackdev/virtuals)** | virtual Python collections over any storage |
| **[invisibles](https://github.com/nustackdev/invisibles)** | transparent remote method invocation |
| **[composables](https://github.com/nustackdev/composables)** | service composition and lifecycle management |

## Ecosystem

One package, `nu`. The fabrics and topologies are submodules (not exposed on the
top-level namespace — import them directly), each behind an optional extra:

| Module | Extra | What |
|--------|-------|------|
| **nu.virtuals** | `nu[virtuals]` | bridges Nu Refs to virtuals Views with RocksDB backend, in-memory or text storages |
| **nu.mem** | `nu[mem]` | in-memory adapter — plain Python dicts as the data bag |
| **nu.distributed** | `nu[distributed]` | distribution via Ray + invisibles |

## Status

v0.1.0. APIs will break. No backwards compatibility guarantees.

Two production systems run on Nu today:

- A financial platform processing thousands of distributed transactions per second across 2 machines
- A reactive knowledge base with persistent state and a live UI

## License

MIT
