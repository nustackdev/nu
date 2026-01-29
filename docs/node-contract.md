# Node Initialization Contract

Every class in the `Node` hierarchy **must** call `super().__init__()` with its children.
Failing to do so leaves `_children` uninitialized, which silently breaks tree traversal,
purity detection, and any operation that walks the tree.

## The Rule

```python
# CORRECT - children are registered via super().__init__()
class MyOp(Operation, Morphism[int]):
    def __init__(self, ref, value):
        super().__init__(ref, value)
        self.ref = ref
        self.value = value

# WRONG - _children is never set, tree traversal crashes
class MyOp(Operation, Morphism[int]):
    def __init__(self, ref, value):
        self.ref = ref
        self.value = value
        self._children = (ref, value)  # DO NOT DO THIS
```

## Why It Matters

`Node.__init__(*children)` sets `self._children`. The `children` property reads `_children`.
Tree operations (`preorder`, `find`, `size`, etc.) iterate `.children` on every node.
If a node skips `super().__init__()`, accessing `.children` raises `AttributeError`.

This is especially dangerous because:

- The error only surfaces when something traverses *through* that node (not the node itself).
- `PVAtomic.enter()` walks the entire subtree to check purity. A single missing `_children`
  anywhere in the tree crashes the span before any child executes.
- Expression wrappers like `StrRef(SetCmd(...))` create deep trees where the missing init
  can hide several levels down.

## Inheritance Chain

```
Node[ChildT]              .__init__(*children) -> sets _children
  Exec[ChildT]            no __init__
    Term[T]               no __init__
      LValue[T]           no __init__
        Ref[T]            no __init__  (abstract: resolve, fetch)
      RValue[T]           no __init__
        Morphism[T]       .__init__(*children) -> delegates to Node
          UnaryMorphism    .__init__(operand)
          BinaryMorphism   .__init__(left, right)
          TernaryMorphism  .__init__(first, second, third)
          NAryMorphism     .__init__(*children)
      Fetchable[T]        no __init__
    Flow[ChildT]          no __init__  (default execute: sequential)
    Span[ChildT]          no __init__  (default execute: enter/exit lifecycle)
```

Any class that defines `__init__` must call `super().__init__()` with the appropriate children.
Classes without `__init__` inherit it from their parent -- no action needed.

## Conditional Children

When children depend on arguments, use conditional super calls:

```python
class DictGetOp(Operation, NAryMorphism[V]):
    def __init__(self, operand, key, default=None):
        if default is None:
            super().__init__(operand, key)
        else:
            super().__init__(operand, key, default)
```

## PyRefBase Pattern

`PyRefBase` wraps a source that may be a `Term` or a literal. When the source is a `Term`,
it must be registered as a child so tree traversal can reach it:

```python
class PyRefBase[T](Ref[T]):
    def __init__(self, source: Term[T] | T) -> None:
        if isinstance(source, Term):
            super().__init__(source)
        else:
            super().__init__()
        self._source = source
```

This matters because `.set("Alice")` returns `StrRef(SetCmd(...))`. The `SetCmd` is impure.
If it's not registered as a child of the `StrRef`, `PVAtomic` can't detect impurity and
will incorrectly open a snapshot instead of a transaction.
