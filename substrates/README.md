# Substrates

Substrate packages for everybase. Each substrate models a different integration topology.

The distinction is by **modeling topology** — how resources are addressed and what operations exist — not by transport.

```
Substrate        Topology                  Status
─────────        ────────                  ──────
eb_shape       hierarchical, in-house    exists
eb_service     flat                      wip
eb_table       relational                todo
eb_rest        hierarchical, HTTP        todo
eb_stream      push-based                todo
eb-gql        schema graph              todo
```

See [`docs/substrate-taxonomy.md`](../docs/substrate-taxonomy.md) for the full paradigm map.
