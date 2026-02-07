# Package Hierarchy

## Layers

```
everybase            unified core — contracts + toolbox
  everybase.core     contracts — Term, Flow, Span, Ref, Model, Context
  everybase.abc      toolbox — types, values, morphisms, capabilities, utilities
    ├── eb_shape    document model — shapes, items, collections, navigation
    │     ├── eb-pv      PV storage substrate (path resolution, views, spans, adapters)
    │     └── eb-dict    dict substrate (plain nested dicts, no persistence)
    └── eb_table    relational model — (TBD)
          └── eb-notion    Notion API integration
  │
  ├── eb-flow        flow primitives (Seq, Par, Cond, Loop)
  ├── eb-flow-ext    flow extensions (cancellation, progress)
  └── every-type        extended type refs (Decimal, UUID, datetime, Path)
```

## Directory Layout

```
everybase/            everybase (everybase.core + everybase.abc)
eb-shape/      eb_shape
eb-table/      eb_table
eb-dict/       eb-dict
eb-flow/       eb-flow
eb-flow-ext/   eb-flow-ext
eb-notion/     eb-notion
eb-pv/         eb-pv
pkg-every-stdtypes/   every-type
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
Utilities       ensure_term, tree walking, etc.
```

### eb_shape

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
```

### eb_table

Abstract relational model. Depends on everybase. (TBD)

## Dependency Graph

```
                    everybase
                  (core + abc)
                    /       \
            eb_shape    eb_table
                |             |
            eb-pv     eb_table
            eb-dict       |
                |        eb-notion
          every-type  eb-flow
          eb-flow-ext
```

Key constraints:

- eb_shape and eb_table are siblings -- both depend on everybase
- eb_shape has zero PV imports -- substrate-independent document model
- eb_table has zero PV imports -- independent data model
- eb-pv depends on eb_shape (PV substrate: persistent, reactive)
- eb-dict depends on eb_shape (dict substrate: plain dicts, no reactivity)
- eb-notion will depend on eb_table (relational adapter)
