---
title: Fabrics
---

A **Fabric** is the substrate a Ref lives on. One page per Fabric: the Refs it ships, the Interactions on top of them, the shape of what it stores.

| Fabric | Module | What |
| --- | --- | --- |
| [mem](mem.md) | `nu.mem` | In-process fabric: plain nested Python dicts as the data bag. Zero setup. |
| [virtuals](virtuals.md) | `nu.kv` | Virtual collections over any KV backend. Persistent, paged, view-composable. |
| [ui](ui.md) | `nu.ui` | Reactive UI fabric: shape trees rendered live in the browser. |
| [ray](ray.md) | `nu.ray` | Distributed fabric backed by Ray actors and object refs. |
| [invisibles](invisibles.md) | `nu.invisibles` | Transparent remote objects: local calls, remote execution. |
