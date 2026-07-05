# Refs

A Ref is a name for a location, plus a Nu atom that self-yields the value at that location. One kind, two roles. The role is decided by the slot the Ref sits in, not by the Ref itself.

This guide covers what a Ref is made of, the substrate contract every Fabric implements, and the conventions that keep the whole thing coherent.

## The four layers

A Ref stacks four layers, top to bottom:

- **form** — the fluent surface: `store`, `erase`, `exists`, `missing`, `[k]`, `.attr`, `on_change`. Pure mixins that contribute the DSL and nothing else.
- **blueprint** — the abstract shape Refs: seven families (Item, Mapping, Sequence, Set, Shape, ShapesMapping, ShapesSequence) times three tiers (Base, Mutable, Reactive). Each blueprint weaves a Form mixin with the hierarchical base.
- **substrate** — the concrete Fabric Refs that read and write storage. Mem, virtuals, nudle, io, context.
- **connective** — the interactions that drive Refs at runtime, the tree passes that rewrite them, the atomicity and Navigator routing.

The form and blueprint layers are shared. The substrate is where a Fabric plugs in.

## Hierarchical vs flat

A Ref is either hierarchical or flat, decided by whether the Fabric has a hierarchy.

| Domain | Hierarchical? | Address shape |
| ------ | ------------- | ------------- |
| shape, mem, virtuals | yes | parent chain plus per-level key |
| nudle | yes | Page then Section then leaf, over a ws path |
| context attr | no | one key into the context attrs |
| context service | no | one service type |
| io stdio | no | one stream, intrinsic |

A hierarchical Ref holds its parent in the tree, in its first child slot. Subsequent child slots hold keys. The parent lives inside-out: `email` on top, `user` deepest in the parent chain, even though you write it outside-in (`user.profile.email`). Nesting recurses for free: in `users[otherref[q]].profile`, `otherref[q]` sits in a value slot so it reads; its own parent stays structural.

A flat Ref has no parent slot. Some flat Refs (stdio) have no address child at all — the stream name lives in the payload. The same generic code handles both hierarchical and flat.

## Slot marks

A Ref declares one slot mark of its own: `structural`. A hierarchical Ref marks its parent slot structural. A flat Ref leaves it empty.

`structural` says: this slot holds address structure, not a value to evaluate. Generic passes skip structural slots when emitting effects and still recurse into them — a Ref used as a dynamic key inside a parent chain is still collected as a READ. `structural` sits outside the effect system; it is not a third effect, because the slot never evaluates and no READ ever arises.

A Ref never declares `mutates`. Producing an address must not transform Context, so a Ref has no write slots. Writing happens one level up, in the op atom that holds the Ref (a `Store`, a `Copy`, a `Swap`).

Reactive queries (`OnChange`, `React`, nudle `Changed`) also mark their source slot structural. Subscribing resolves the address to open the handle; it never fires the value thunk. A structural slot never forces a Snapshot: subscribe registers on the live observer, and opening the view handle takes its Context from the execution scope.

## StructuredRef

`StructuredRef` is the public hierarchical base. Every hierarchical Fabric Ref inherits it and implements against it. It gives you:

- parent access via the first child slot, marked structural
- address resolution that recurses the parent slot and evaluates the key slots
- one data-driven navigation path (see below)
- the value-boundary hooks `_lift` and `_lower`

All of a Ref's identity — kind, children, payload — lives on the term's canonical parts. Substrate parameters (owner shape, root shape, segment, view type, value type, facet, shape type) live in the payload; private properties dip in and expose them. Because the payload participates in term equality, structurally equal Refs stay equal after any tree rewrite.

## The substrate contract

Two parts: one universal core, and per-Fabric capabilities.

### Core

Every Ref, every Fabric, implements one method: **resolve address**, sync and async. It recurses the parent slot (structural) and evaluates the key slots (value). Pinned signature.

That is the only universal. Read is not core — a nudle read is a network round-trip, io `readline` is consuming, service is a type lookup. Making read universal would flatten these back into a single incompatible method.

### Capabilities

Each Fabric declares the verbs it supports. Interactions dispatch on declared capability. A Ref lacking a capability fails at compile, not at runtime.

| Fabric | Capabilities |
| ------ | ------------ |
| mem, virtuals | `_load`, `_write`, `_erase`, `_materialize`, each with an async twin |
| nudle | `_store`, `_append`, `_changed`, async-only |
| io | `_write`, `_readline` |
| context service | read-only value; method calls are separate atoms |

`_load` is the dual-role value fetch: it fires when a Ref appears as a value child. `_materialize` is the write-path parent op. It is **fetch-or-create**: a three-deep write into empty storage must vivify the intermediate parents. Do not conflate it with a plain parent fetch — the "or create" is the whole point.

The contract is enforced by a typing Protocol with pinned signatures, plus a property test: a flattened chain and its original chain must load the same value in the same Context.

## Value boundary

Every Ref has a value type. The boundary between raw storage and typed value is one symmetric pair on that type.

- `_lift` — raw storage value to typed value (a date Ref's raw string to a `date`). Runs on every read path.
- `_lower` — typed value to storage form. Runs on every write path.

`_write` and `store` take one canonical input: the typed value. A Nu child means compose, then lower the yield. There is no tri-modal accept of value, Nu, or raw — a wrap-or-not guess by python isinstance never crosses a Nu boundary cleanly. The Ref knows its type; the author never does a wrap or unwrap dance.

## Navigation

Item lookup (`[k]`) and attribute lookup (`.attr`) are one concern with typing. `StructuredRef` gives one data-driven path that:

1. constructs the child with the convention — parent slot points at self, marked structural
2. carries substrate params from the slot, no per-Fabric method override
3. is typed to return the value type `T`, so the IDE autocompletes the value's surface

The return type is `Ref[T]` that is also statically `T` via the Form mixin — `.store()` and `.exists()` stay reachable, and value methods autocomplete. The mixin must not break isinstance-Ref: every tree pass relies on it.

Substrate override happens through a single wrap hook plus a generic result type bound per tier. Item lookup is defined once per collection blueprint. Each tier defaults to its domain item Ref; substrates override the hook. Same shape across mapping, sequence, shapes-mapping, and shapes-sequence.

## Inline as an optimization

Inlining folds a static Ref chain into a flat Ref with a pre-resolved path tuple. Runtime resolution walks the on-tree chain directly, so inlining is an optimization, not a correctness requirement. The flat Ref stays only where flattening measurably helps.

If you touch inlining:

- **Fold, don't climb.** Compose the child's already-flattened parent with this node's own address; re-base dynamic-segment indices. There is no parent attribute to walk — the parent is a tree child.
- `_lift` runs on the flat path too. The value type is known from the Ref's kind, so the flat path can and must call it.
- Cross-Fabric refs-in-keys resolve as an ordinary subtree flattened in the same pass.
- Some Refs are non-flattenable — a queue Ref, for example, because flattening kills its vivification semantics. Guard by declared capability, not by an isinstance list.

## Public and private naming

A Ref carries two surfaces on one object:

1. **User-facing DSL**: `store`, `erase`, `exists`, `[]`, `.attr`, `on_change`, arithmetic, comparisons.
2. **Value type surface**: `PurePath.parent`, `Decimal.quantize`, whatever the value type exposes.

The value surface is public and not ours to rename, so any public machinery name risks colliding with it. Rule: **core machinery is private, only user-facing interactions are public.** Address resolution, load, write, erase, materialize, lift, lower, root shape, owner shape, segment, value type — all underscore.

Two exceptions. `compile` stays non-underscore: it is the universal Term protocol the engine calls generically, not Ref-specific. `StructuredRef` stays public: it is the contract every Fabric implements against.

Sync and async pair spelling: `foo` and `afoo`, one spelling per concept across every Fabric.

## Adding a Fabric

Order for a new Fabric ref layer:

1. Extend `StructuredRef` if hierarchical, `Ref` if flat. Mark the parent slot structural on hierarchical Refs; leave it empty on flat.
2. Put all identity state in the payload; expose it via private properties.
3. Implement the core: resolve address, sync and async, with the pinned signature.
4. Declare capabilities. Storage Fabrics: `_load`, `_write`, `_erase`, `_materialize` (fetch-or-create). Nudle-shaped Fabrics: `_store`, `_append`, `_changed`, async-only.
5. Define `_lift` and `_lower` on the value type. Lift runs on every read path, including the flat one.
6. Data-drive navigation via the wrap hook. No hand-built per-tier overrides.
7. Add functional tests against the real backend via the suite's fixtures. Ten to twenty tests, moving from simple through nested navigation, dynamic keys, cross-Fabric keys, refs-in-keys, and reactive sources.

The invariants your tests must gate on:

- effect sets are byte-identical to a hand-written baseline
- a three-deep write vivifies into empty storage
- a cross-Fabric-key repro (mem Ref used as a virtuals key) resolves and reads
- a flattened chain reads the same value as the original chain in the same Context
