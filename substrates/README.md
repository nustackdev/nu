# Substrates

Substrate packages for everybase. Each substrate models a different integration topology.

The distinction is by **modeling topology** — how resources are addressed and what operations exist — not by transport.

```
Substrate        Topology                  Status
─────────        ────────                  ──────
everyshape       hierarchical, in-house    exists
everyservice     flat                      wip
everytable       relational                todo
everyrest        hierarchical, HTTP        todo
everystream      push-based                todo
every-gql        schema graph              todo
```

See [`_docs/substrate-taxonomy.md`](../_docs/substrate-taxonomy.md) for the full paradigm map.
