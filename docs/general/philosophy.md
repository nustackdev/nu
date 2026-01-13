# everyshape

## Data Topology

Here is a location, here is another location, here is the path between them. The locations can hold anything. The paths can traverse anything. The topology itself is the invariant.

everyshape encodes data topology.

## Three Separations

**Location from Computation.** A ref points somewhere. A value computes something. They are distinct. You can have a location without reading it. You can build computation without a location. Combine them or don't.

**Structure from Storage.** Views define how data behaves — dict semantics, list semantics, set semantics. Storage defines where bytes live. The same view can sit on memory, disk, network, sharded cluster. The same storage can present different views.

**Protocol from Implementation.** Layer 4 defines what refs and values must do. It says nothing about how. Implement the protocol, gain the composition. The system doesn't know or care what's behind the interface.

## Views Are Infinite

A view is a lens over storage. It interprets raw keys as structure.

Dict view sees `{"a": 1, "b": 2}`. List view sees `[1, 2, 3]`. Set view sees `{1, 2, 3}`. But these are just the obvious ones.

A view can see a B-tree. A view can see a time-series with automatic bucketing. A view can see a graph with adjacency encoded in key prefixes. A view can see a sparse tensor.

The view protocol is fixed. What views can represent is not. Any structure that can be projected onto key-value pairs can have a view. Any optimization that can be expressed in how keys are laid out can be encoded.

This is the extensibility that matters. Not plugin architectures. Not configuration options. The ability to define entirely new structural interpretations without changing anything above or below.

## The Term Layer as Algebra

Layer 4 is algebraic. It defines:

- Ref — element of the location set
- Value — element of the computation set
- Operation — pure morphism (computation → computation)
- Command — impure morphism (computation → effect)

These compose. Refs chain through navigation. Values chain through operators. Operations chain through application. The algebra is closed — combining terms produces terms.

The specific types (IntValue, FloatRef, GetOp) are inhabitants. The layer defines the algebra. You populate it.

## Shapes as Declarations

A shape declares: at this address, this topology exists.

```python
class Market(Shape):
    symbols = ShapesDictSlot(Symbol)
```

This says: under "symbols", there is a dict-shaped topology where values have Symbol topology.

It doesn't say how to store it. It doesn't say how to validate it. It doesn't say what Symbol means. It declares the nesting relationship.

Shapes are topology declarations. Slots are local topology specifiers. Together they describe the full traversal graph.

## Lazy by Construction

Nothing evaluates until asked. Building `a.get() + b.get()` constructs a tree with three nodes. The tree is data. It can be inspected, transformed, optimized, serialized.

Execution is a separate act. You can build many trees. You can combine trees. You can analyze trees. When you want a result, you execute.

This separation means the system can see your intent before committing to action. Batching, caching, reordering — these become transformations on trees, not runtime heuristics.

## The Stack

```
Shape  — topology declaration
Term   — computation algebra
View   — structure interpretation
Container — hierarchy maintenance
Storage — byte persistence
```

Each layer depends only on the layer below. Each layer is independently replaceable. The contracts between layers are thin — just protocols.

This isn't modular design for its own sake. It's recognition that these concerns are orthogonal. How you declare structure shouldn't know how you persist bytes. How you compute shouldn't know how you interpret keys.

## What Flows Through

Define a new view. It works with existing shapes, existing terms, existing storage.

Define a new value type. It works with existing refs, existing views, existing shapes.

Define a new storage backend. It works with existing everything.

The protocols are the stable points. Implementations flow through them. This is why the term layer is mostly abstract — it's the algebra, not the inhabitants.

## Data Programming

Traditional code operates on data. Load it, transform it, store it.

This inverts it. Data topology becomes the program structure. Shapes are the nouns. Terms are the verbs. Views are the grammar. You don't write code that manipulates data. You write data that describes manipulation.

The expression tree is the program. Execution interprets it. The program is inspectable, composable, transmittable. It's data about data operations.

---

Topology as type. Algebra as layer. Structure as protocol.
