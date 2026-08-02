---
title: nu.shape
---

Shape DSL: declares hierarchical document structures (`Shape`, `Slot`) and the
fabric-level read/write atoms that operate on any Ref in the 3-tier Ref matrix
(21 Ref blueprints, 7 families x 3 tiers). `Shape` and `Slot` are flat-exported;
fabric atoms and the Ref blueprints stay namespaced under `nu.shape.*`.

## DSL

`from nu import Shape, Slot`

Metaclass-driven: `ShapeMeta` collects `Slot` definitions at class-definition
time and replaces them with `SlotDescriptor`s. `Shape` is never instantiated —
all access is at class level.

| Name           | Sort  | Signature                                    | Effect | Meaning                                                    |
| -------------- | ----- | --------------------------------------------- | ------ | ----------------------------------------------------------- |
| Shape          | class | `class Foo(Shape): ...`                       | n/a    | declarative structure definition using Slots                |
| Slot           | class | `Slot(ref_cls, props=None, **kwargs)`         | n/a    | factory carrying a Ref class + kwargs; `create_ref` builds the Ref |
| ShapeMeta      | class | metaclass of `Shape`                          | n/a    | collects Slots, stamps `TypeInfo` from annotations, installs descriptors |
| SlotDescriptor | class | descriptor installed per slot                 | n/a    | returns a Ref when a slot name is accessed on a Shape class  |

## Fabric atoms

`from nu.shape import Load, Exists, Missing, Extract, AdvanceCursor, SetCmd, Erase, PrimitiveSet`

Polymorphic on Ref class — one set of atoms works over every Ref in the
3-tier matrix. Reactive queries (`OnChange`, `OnChildChange`,
`OnChildrenChange`, `OnDescendantsChange`, `OnPrimitiveChange`) live in
`nu.core.reactive`, reached through the shape Form mixins, not here.

| Name          | Sort          | Signature                    | Effect | Meaning                                                        |
| ------------- | ------------- | ----------------------------- | ------ | --------------------------------------------------------------- |
| Load          | ScalarQuery   | `Load(ref)`                   | pure   | value at the slot-0 Ref's address (EMPTY if unbound)             |
| Exists        | ScalarQuery   | `Exists(ref)`                 | pure   | True if the slot-0 Ref's address is bound                       |
| Missing       | ScalarQuery   | `Missing(ref)`                | pure   | True if the slot-0 Ref's address is unbound                     |
| Extract       | ScalarQuery   | `Extract(ref)`                | pure   | materialise the full subtree at the Ref into a plain Python value |
| AdvanceCursor | ScalarQuery   | `AdvanceCursor(ref, cursor)`  | pure   | next key after cursor on an ordered view; `None` starts from the beginning |
| SetCmd        | ScalarCommand | `SetCmd(ref, value)`          | WRITE  | write value to the slot-0 structured Ref's address              |
| Erase         | ScalarCommand | `Erase(ref)`                  | WRITE  | remove the slot-0 structured Ref from its fabric                |
| PrimitiveSet  | ScalarCommand | `PrimitiveSet(ref, value)`    | WRITE  | write value as a single primitive blob, bypassing compound decomposition |

## Ref blueprints

`from nu.shape.refs import ItemRef, MappingRef, SequenceRef, SetRef, ShapeRef, ShapesMappingRef, ShapesSequenceRef, ...`

21 Ref blueprints — 7 families x 3 tiers — plus the abstract `StructuredRef`
base for substrate authors. `StructuredRef` encodes a hierarchical path into
a shape fabric: `children[0]` is the parent (structural, address only),
`children[1]` is this Ref's own address.

Tiers per family: **Base** (read + exists/missing), **Mutable** (+ write/erase
+ collection mutations), **Reactive** (+ `on_change` family).

| Family        | Base              | Mutable                  | Reactive                  | Meaning                              |
| ------------- | ----------------- | ------------------------ | -------------------------- | ------------------------------------- |
| Item          | ItemRef           | MutableItemRef            | ReactiveItemRef            | leaf typed value                      |
| Mapping       | MappingRef        | MutableMappingRef         | ReactiveMappingRef         | key-value container                   |
| Sequence      | SequenceRef       | MutableSequenceRef        | ReactiveSequenceRef        | ordered element container             |
| Set           | SetRef            | MutableSetRef             | ReactiveSetRef             | unordered unique-element container    |
| Shape         | ShapeRef          | MutableShapeRef           | ReactiveShapeRef           | structured named-slot container       |
| ShapesMapping | ShapesMappingRef  | MutableShapesMappingRef   | ReactiveShapesMappingRef   | mapping whose values are shapes       |
| ShapesSequence| ShapesSequenceRef | MutableShapesSequenceRef  | ReactiveShapesSequenceRef  | sequence whose elements are shapes    |

> `StructuredRef` (base class, `nu.shape.refs.StructuredRef`) is re-exported for
> substrate authors extending it directly; not used directly in application code.
