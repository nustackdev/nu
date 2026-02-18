# everybase

Computation model and common base classes.

## What

Two subpackages -- contracts and base implementations:

```
everybase/
├── core/   — contracts: Node, Exec, Term, Flow, Span, Sentinel, Ref, Context
└── abc/    — base implementations: types, values, morphisms, capabilities
```

**core/** defines the computation model. `Term` (computation), `Flow` (ordering), `Span` (grouping) are abstract -- concrete implementations live downstream.

**abc/** provides reusable building blocks -- type bases, value wrappers, capability protocol+base pairs, common morphisms, and utilities.

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
everybase/      — contracts + base implementations
substrates/     — integration substrates (eb_shape, eb_table, eb_stream)
pkgs/           — utility + extension packages (eb-pv, eb-flow, ...)
```

## Development

Part of [everybase](https://github.com/everyabc/everybase).

```bash
make test-pkg PKG=everybase
```
