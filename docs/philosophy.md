# Philosophy

## Data Topology

Here is a location, here is another location, here is the path between them. The locations can hold anything. The paths can traverse anything. The topology itself is the invariant.

## Three Separations

**Location from Computation.** A ref points somewhere. A value computes something. They are distinct. You can have a location without reading it. You can build computation without a location. Combine them or don't.

**Structure from Storage.** Views define how data behaves — dict semantics, list semantics, set semantics. Storage defines where bytes live. The same view can sit on memory, disk, network, sharded cluster. The same storage can present different views.

**Protocol from Implementation.** Contracts define what refs and values must do. They say nothing about how. Implement the protocol, gain the composition. The system doesn't know or care what's behind the interface.

## Why Three Primitives

Every program answers three orthogonal questions:

1. **What** happens at each step? → Term
2. **When** does each step run relative to others? → Flow
3. **Which** steps are related toghether? → Span

These concerns are independent. Changing the order (Flow) doesn't change the computation (Term). Adding shared context (Span) doesn't change what is computed or in what order.

Each primitive owns exactly one question:

```
          computes?    orders?    shares?
Term         x
Flow                     x
Span                                x
```

## Shapes as Declarations

A shape declares: at this address, this topology exists.

```python
class Market(Shape):
    symbols = ShapesDictRef.slot(Symbol)
```

This says: under "symbols", there is a dict-shaped topology where values have Symbol topology.

It doesn't say how to store it. It doesn't say how to validate it. It doesn't say what Symbol means. It declares the nesting relationship.

Shapes are topology declarations. Ref.slot() calls are local topology specifiers. Together they describe the full traversal graph.

## Lazy by Construction

Nothing evaluates until asked. Building `a.get() + b.get()` constructs a tree with three nodes. The tree is data. It can be inspected, transformed, optimized, serialized.

Execution is a separate act. You can build many trees. You can combine trees. You can analyze trees. When you want a result, you execute.

This separation means the system can see your intent before committing to action. Batching, caching, reordering — these become transformations on trees, not runtime heuristics.

## What Flows Through

Define a new view. It works with existing shapes, existing terms, existing storage.

Define a new value type. It works with existing refs, existing views, existing shapes.

Define a new storage backend. It works with existing everything.

The protocols are the stable points. Implementations flow through them.

## Data Programming

Traditional code operates on data. Load it, transform it, store it.

This inverts it. Data topology becomes the program structure. Shapes are the nouns. Terms are the verbs. Views are the grammar. You don't write code that manipulates data. You write data that describes manipulation.

The expression tree is the program. Execution interprets it. The program is inspectable, composable, transmittable. It's data about data operations.

---

Topology as type. Algebra as layer. Structure as protocol.
