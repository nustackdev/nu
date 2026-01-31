# Package Hierarchy

## Layers

```
everyabc            contracts — Term, Flow, Span, Ref, Shape, Slot, Context
  ├── everybase     toolbox — types, values, morphisms, capabilities, utilities
  ├── everyshape    document model — ShapeMeta, ShapeBase, SlotDescriptor
  └── everytable    relational model — (TBD)
    │
    ├── every-pv          PV storage adapter + views (ShapeBase → PV refs)
    ├── every-flow        flow primitives (Seq, Par, Cond, Loop)
    ├── every-flow-ext    flow extensions (cancellation, progress)
    ├── every-type        extended type refs (Decimal, UUID, datetime, Path)
    ├── every-kv          key-value store protocol
    ├── every-adapters    storage/codec/observer backends
    └── every-notion      Notion API integration (everytable adapter)
```

## Core Packages

### everyabc

Pure contracts. No implementations, no external deps.

```
Node            immutable tree node
Executable      typed subtree
Term            computation (execute → result)
  LValue        addressable location (resolve → substrate location)
    Ref         typed reference (fetch → value)
  RValue        evaluable expression
    Morphism    transformation (apply → result)
Flow            ordering (Seq, Par, Cond, Loop)
Span            cohesion boundary (enter/exit context)
Context         type-keyed handle container
Shape           marker base for structure definitions
Slot            abstract slot (create_ref → Ref)
Sentinel        EMPTY / INVALID propagation
```

### everybase

Universal building blocks. Depends only on everyabc.

```
Types           IntType, StrType, FloatType, BoolType, BytesType
Values          IntValue, StrValue, FloatValue, BoolValue, BytesValue, ...
Capabilities    loc_item (get/set/delete/exists)
                loc_collection (filter/find/map)
                loc_reactive (on_change observers)
Morphisms       base morphism implementations
Utilities       ensure_term, tree walking, etc.
```

### everyshape

Abstract document model. Depends only on everyabc.

```
ShapeMeta       metaclass — collects Slots at class creation,
                replaces them with SlotDescriptors
ShapeBase       base class for declarative shape definitions
                (Shape + ShapeMeta); never instantiated
SlotDescriptor  descriptor — bridges slot definitions to refs at runtime
                (slot.create_ref on attribute access)
```

### everytable

Abstract relational model. Depends only on everyabc. (TBD)

## Dependency Graph

```
                    everyabc
                   /    |    \
           everybase  everyshape  everytable
              |          |            |
              |      every-pv     every-notion
              |          |
          every-flow  every-type
          every-kv    every-adapters
          every-flow-ext
```

Key constraints:

- everyshape has zero PV imports — it knows nothing about storage
- everytable has zero PV imports — independent data model
- every-pv depends on everyshape (concrete PV refs for shapes)
- every-notion will depend on everytable (relational adapter)
- everybase and everyshape are siblings, not parent-child
