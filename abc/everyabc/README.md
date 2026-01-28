# everyast

Abstract tree construction, traversal, and transformation.

## What

Two layers — pure tree structure and node contracts:

```
everyast/
├── ast/    — generic Node, walk, transform, query
└── defs/   — Exec, Term, Flow, Span, Sentinel
```

**ast/** is a zero-semantics tree library. `Node[_ChildT]` is generic — subclasses get properly typed children, iteration, and indexing via `Self` returns.

**defs/** adds node type contracts on top. `Exec(Node["Exec"])` is the base for all typed AST nodes. `Term` (computation), `Flow` (ordering), `Span` (grouping) are abstract — concrete implementations live downstream.

## API

```python
from everyast import Node, Exec, Term, Flow, Span

# Tree operations
from everyast import preorder, postorder, bfs, leaves, ancestors
from everyast import map_children, map_nodes, replace, wrap, unwrap, graft, prune
from everyast import find, find_first, count, size, depth
from everyast import compose, apply

# Sentinels
from everyast import EMPTY, INVALID, is_empty, is_invalid, is_sentinel
```

## Layer stack

```
everyast      — Node, walk, transform, query, node contracts
everytree     — (future) needs algebra, deformations
every         — execution contracts, protocols
everybase     — concrete implementations
```

## Development

Part of [everybase](https://github.com/everyabc/everybase).

```bash
make test-pkg PKG=abc/everyast
```
