# Meta

Tree-level meta-programming tools. Walk, query, and rewrite Nu trees. Core only — shapes and ext/ not included.

## Walk

| Name        | Module           | Signature                | Meaning                                         |
| ----------- | ---------------- | ------------------------ | ----------------------------------------------- |
| `preorder`  | `nu.tree.walk`   | `preorder(root)`         | depth-first pre-order iteration                 |
| `postorder` | `nu.tree.walk`   | `postorder(root)`        | depth-first post-order iteration                |
| `bfs`       | `nu.tree.walk`   | `bfs(root)`              | breadth-first iteration                         |
| `leaves`    | `nu.tree.walk`   | `leaves(root)`           | yield leaf nodes only                           |
| `ancestors` | `nu.tree.walk`   | `ancestors(target, root)` | path from root to a target node (exclusive)    |

## Query

| Name         | Module          | Signature                 | Meaning                              |
| ------------ | --------------- | ------------------------- | ------------------------------------ |
| `find`       | `nu.tree.query` | `find(root, pred)`        | all nodes matching predicate         |
| `find_first` | `nu.tree.query` | `find_first(root, pred)`  | first node matching predicate, or None |
| `count`      | `nu.tree.query` | `count(root, pred=None)`  | count matching nodes (None = all)    |
| `size`       | `nu.tree.query` | `size(root)`              | total node count                     |
| `depth`      | `nu.tree.query` | `depth(root)`             | maximum tree depth (leaf = 0)        |

## Rewrite

| Name               | Module            | Signature                                | Meaning                                                  |
| ------------------ | ----------------- | ---------------------------------------- | -------------------------------------------------------- |
| `compose`          | `nu.tree.rewrite` | `compose(*transforms)`                   | chain transforms left-to-right                           |
| `apply`            | `nu.tree.rewrite` | `apply(root, *transforms)`               | run a sequence of transforms on root                     |
| `map_children`     | `nu.tree.rewrite` | `map_children(node, fn)`                 | transform direct children only                           |
| `map_nodes`        | `nu.tree.rewrite` | `map_nodes(root, fn, order=...)`         | transform every node, top-down or bottom-up              |
| `replace`          | `nu.tree.rewrite` | `replace(root, pred, replacement)`       | swap nodes matching predicate                            |
| `wrap`             | `nu.tree.rewrite` | `wrap(root, pred, wrapper)`              | wrap nodes matching predicate                            |
| `unwrap`           | `nu.tree.rewrite` | `unwrap(root, pred)`                     | splice out single-child wrappers                         |
| `graft`            | `nu.tree.rewrite` | `graft(root, target, subtree)`           | replace one specific node (by identity) with a subtree   |
| `prune`            | `nu.tree.rewrite` | `prune(root, pred)`                      | drop subtrees matching predicate                         |
| `conditional_wrap` | `nu.tree.rewrite` | `conditional_wrap(root, pred, wrapper)`  | wrap biggest matching subtree at each level, no recursion inside |
