# Package Hierarchy

## Layers

```
everybase               unified core package
  everybase.core        contracts — Term, Flow, Span, Ref, Model, Context
  everybase.abc         toolbox — types, values, morphisms, capabilities, flows
  everybase.shape       document topology — shapes, items, collections, reactive flows
  everybase.table       relational topology — (TBD)
  everybase.graph       graph topology — (TBD)

eb_virtuals                   PV adapter (path resolution, views, spans, adapters)
eb_dict                 Dict adapter (plain Python dicts)
```

## Directory Layout

```
src/everybase/          unified core package
├── core/               kernel
├── abc/                toolbox
├── shape/              document topology
├── table/              relational topology (stub)
└── graph/              graph topology (stub)

ext/
├── eb-virtuals/              PV adapter
├── eb-dict/            Dict adapter
├── eb-datetime/        Datetime types
├── eb-math/            Math types
├── eb-fin/             Financial types
├── eb-path/            Path types
├── eb-uuid/            UUID types
├── eb-shape-lens/      Terminal shape viewer
└── eb-tree-view/       HTML tree explorer
```

## Core Package

### everybase

Unified core package. Minimal deps (attrs only).

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

#### everybase.shape (document topology)

Document model. Part of everybase (no separate package).

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

#### everybase.table (relational topology)

Abstract relational model. (TBD)

## Dependency Graph

```
              everybase
     (core + abc + topologies)
           /          \
        eb_virtuals        eb_dict
   (PV adapter)  (dict adapter)
```

Key constraints:

- Topologies (shape, table, graph) are inside everybase — no separate packages
- shape has zero PV imports — topology-independent document model
- eb_virtuals and eb_dict are adapters — they wire topologies to storage backends
- Flows live in everybase.abc (non-reactive) and everybase.shape (reactive)
