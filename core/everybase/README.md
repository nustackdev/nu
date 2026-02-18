# everybase

Computation model and common base classes.

## What

Two subpackages — contracts and base implementations:

```
everybase/
├── core/   — contracts: Node, Exec, Term, Flow, Span, Sentinel, Ref, Context
└── abc/    — base implementations: types, values, morphisms, capabilities, flows
```

**core/** defines the computation model. `Term` (computation), `Flow` (ordering), `Span` (grouping) are abstract — concrete implementations live downstream.

**abc/** provides reusable building blocks — type bases, value wrappers, capability protocol+base pairs, common morphisms, flow primitives, and utilities.

## API

```python
from everybase import Node, Exec, Term, Flow, Span

# Tree operations
from everybase import preorder, postorder, bfs, leaves, ancestors
from everybase import map_children, map_nodes, replace, wrap, unwrap, graft, prune
from everybase import find, find_first, count, size, depth

# Sentinels
from everybase import EMPTY, INVALID, is_empty, is_invalid, is_sentinel

# Base implementations
from everybase.abc import IntType, StrType, FloatType
from everybase.abc import IntValue, StrValue, FloatValue
```

## Layer stack

```
core/everybase      — contracts + base implementations
core/everyshape     — declarative document model
core/everypv        — polymorphic views over KV storages
core/everytable     — relational data model (stub)
core/everystream    — push-based event streams (stub)
core/everygraph     — graph data model (stub)
pkgs/               — optional type + tool packages
```

## Development

Part of [everybase](https://github.com/everyabc/everybase).

```bash
make test-pkg PKG=everybase
```
