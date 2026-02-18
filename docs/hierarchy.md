# Package Hierarchy

## Layers

```
everybase            unified core — contracts + toolbox
  everybase.core     contracts — Term, Flow, Span, Ref, Model, Context
  everybase.abc      toolbox — types, values, morphisms, capabilities, flows
    ├── everyshape    document model — shapes, items, collections, reactive flows
    │     └── everypv      PV storage substrate (path resolution, views, spans, adapters)
    ├── everytable    relational model — (TBD)
    ├── everystream   push-based event streams — (TBD)
    └── everygraph    graph data model — (TBD)
```

## Directory Layout

```
core/
├── everybase/      everybase (everybase.core + everybase.abc)
├── everyshape/     everyshape
├── everypv/        everypv
├── everytable/     everytable (stub)
├── everystream/    everystream (stub)
└── everygraph/     everygraph (stub)

pkgs/
├── eb-datetime/    Datetime types
├── eb-math/        Math types
├── eb-fin/         Financial types
├── eb-path/        Path types
├── eb-uuid/        UUID types
├── eb-shape-lens/  Terminal shape viewer
└── eb-tree-view/   HTML tree explorer
```

## Core Package

### everybase

Unified core package with two subpackages.

#### everybase.core (contracts)

Pure contracts. No implementations, no external deps.

```
Node            immutable tree node
Executable      typed subtree
Term            computation (execute -> result)
  LValue        addressable location (resolve -> substrate location)
    Ref         typed reference (fetch -> value)
  RValue        evaluable expression
    Morphism    transformation (apply -> result)
Flow            ordering (Seq, Par, Cond, Loop)
Span            cohesion boundary (enter/exit context)
Context         type-keyed handle container
Model           marker base for structure definitions (Shape, Table extend this)
Sentinel        EMPTY / INVALID propagation
```

#### everybase.abc (base implementations)

Universal building blocks.

```
Types           IntType, StrType, FloatType, BoolType, BytesType
Values          IntValue, StrValue, FloatValue, BoolValue, BytesValue, ...
Capabilities    loc_item (get/set/delete/exists)
                loc_collection (extract/store/length/clear/exists)
                loc_reactive (on_change observers)
Morphisms       base morphism implementations
Flows           Seq, If, While, ForRange, Parallel, TryCatch, etc.
Utilities       ensure_term, tree walking, etc.
```

### everyshape

Document model. Depends on everybase.

```
Shape System    ShapeMeta, Shape (extends Model), SlotDescriptor

Slot            universal slot that creates any Ref type (used by Ref.slot())

Ref Base        Ref (document-model ref contract: address, parent, shape, slot())

Items           ItemRef -> MutableItemRef -> ReactiveItemRef
                (typed value holders with CRUD + observation)

Collections     ShapeRef -> MutableShapeRef -> ReactiveShapeRef
                (structured containers with attribute navigation)

                MappingRef -> MutableMappingRef -> ReactiveMappingRef
                (key-value containers)

                SequenceRef -> MutableSequenceRef -> ReactiveSequenceRef
                (ordered containers)

                ShapesListRef / ShapesDictRef (+ Mutable / Reactive)
                (homogeneous shape collections)

Flows           React, ReactForever, ReactWhile (reactive flows)
```

### everytable

Abstract relational model. Depends on everybase. (TBD)

## Dependency Graph

```
                    everybase
                  (core + abc)
                  /     |     \
          everyshape  everytable  everystream  everygraph
              |
          everypv
```

Key constraints:

- everyshape, everytable, everystream, everygraph are siblings — all depend on everybase
- everyshape has zero PV imports — substrate-independent document model
- everytable has zero PV imports — independent data model
- everypv depends on everyshape (PV substrate: persistent, reactive)
- Flows live in everybase.abc (non-reactive) and everyshape (reactive)
