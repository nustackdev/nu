# everyast

Abstract tree construction, traversal, and transformation.

The foundational layer for AST construction — pure tree structure and operations with no domain semantics. Downstream packages build on this to define typed node hierarchies (e.g., topology programming primitives).

## Usage

```python
from everyast import Node, preorder, map_nodes, find, depth
```

## Development

Part of [everybase](https://github.com/everyabc/everybase).

```bash
make test-pkg PKG=abc/everyast
```
