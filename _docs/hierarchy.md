# Package Hierarchy

## Layers

```
everyabc            contracts — Term, Flow, Span, Ref, Model, Context
  └── everybase     toolbox — types, values, morphisms, capabilities, utilities
        ├── everyshape    document model — shapes, items, collections, navigation
        │     ├── every-pv      PV storage substrate (path resolution, views, spans, adapters)
        │     └── every-dict    dict substrate (plain nested dicts, no persistence)
        └── everytable    relational model — (TBD)
              └── every-notion    Notion API integration
    │
    ├── every-flow        flow primitives (Seq, Par, Cond, Loop)
    ├── every-flow-ext    flow extensions (cancellation, progress)
    └── every-type        extended type refs (Decimal, UUID, datetime, Path)
```

## Directory Layout

```
core-every/           everyabc
core-every-bases/     everybase
pkg-every-shape/      everyshape
pkg-every-table/      everytable
pkg-every-dict/       every-dict
pkg-every-flow/       every-flow
pkg-every-flow-ext/   every-flow-ext
pkg-every-notion/     every-notion
pkg-every-pv/         every-pv
pkg-every-stdtypes/   every-type
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
Model           marker base for structure definitions (Shape, Table extend this)
Sentinel        EMPTY / INVALID propagation
```

### everybase

Universal building blocks. Depends on everyabc.

```
Types           IntType, StrType, FloatType, BoolType, BytesType
Values          IntValue, StrValue, FloatValue, BoolValue, BytesValue, ...
Capabilities    loc_item (get/set/delete/exists)
                loc_collection (extract/store/length/clear/exists)
                loc_reactive (on_change observers)
Morphisms       base morphism implementations
Utilities       ensure_term, tree walking, etc.
```

### everyshape

Document model. Depends on everybase.

```
Shape System    ShapeMeta, Shape (extends Model), SlotDescriptor

Slot            universal slot that creates any Ref type (used by Ref.slot())

Ref Base        ShapeRefBase (document-model ref contract: address, parent, shape, slot())

Items           ItemRef → MutableItemRef → ReactiveItemRef
                (typed value holders with CRUD + observation)

Collections     ShapeRef → MutableShapeRef → ReactiveShapeRef
                (structured containers with attribute navigation)

                MappingRef → MutableMappingRef → ReactiveMappingRef
                (key-value containers)

                SequenceRef → MutableSequenceRef → ReactiveSequenceRef
                (ordered containers)

                ShapesListRef / ShapesDictRef (+ Mutable / Reactive)
                (homogeneous shape collections)
```

### everytable

Abstract relational model. Depends on everybase. (TBD)

## Dependency Graph

```
                    everyabc
                       |
                    everybase
                    /       \
            everyshape    everytable
                |             |
            every-pv     everytable
            every-dict       |
                |        every-notion
          every-type  every-flow
          every-flow-ext
```

Key constraints:

- everyshape and everytable are siblings — both depend on everybase
- everyshape has zero PV imports — substrate-independent document model
- everytable has zero PV imports — independent data model
- every-pv depends on everyshape (PV substrate: persistent, reactive)
- every-dict depends on everyshape (dict substrate: plain dicts, no reactivity)
- every-notion will depend on everytable (relational adapter)
