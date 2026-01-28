# Design Rules

The invariants we commit to. Labeled for cross-referencing.

---

## Composition

```
R1.  Term.children() → list[Term]     Terms compose only with Terms.
R2.  Flow.children() → list[Unit]     Flows compose with any Unit.
R3.  Group.children() → list[Unit]    Groups compose with any Unit.
```

---

## Structure

**S1. Implicit grouping.**
Every direct Term child of a Flow is implicitly wrapped in an Atomic group.
An expression tree is indivisible — like a function call.

```
F(T₁, T₂, ...) is treated as F(Atomic(T₁), Atomic(T₂), ...)
```

This is not substrate policy. It follows from what "one expression" means.

**S2. Group transparency.**
A Group is not a computation. It passes through the value of its contents.
Removing all Groups from a tree does not change what is computed,
only what is shared during computation.

**S3. Term closure.**
Composing Terms yields a Term. The Term algebra is closed.

**S4. Orthogonality.**
Flow does not compute — it only orders.
Group does not order — it only declares cohesion.
Term does not order or share — it only computes.
Each primitive owns exactly one concern.

---

## Resolution

**B1. Needs propagate up.**
A Unit's needs are the union of its own needs and its children's needs.
Groups absorb the needs they provide — those don't propagate further.

**B2. Nearest enclosing Group wins.**
When a Term needs a context type, the executor walks up the tree.
First Group that provides a matching context wins.

**B3. Ephemeral fallback.**
If no Group provides what a Term needs, the executor creates
an ephemeral context from the nearest Substrate. Scoped to the
single expression (per S1).

**B4. Innermost wins.**
Nested Groups override. Inner Group's context shadows outer
for its subtree. Same mental model as variable scoping.

---

## Lifetime

**C1. Lazy open.**
A Group's context is created when the first child that needs it executes.
Not at Group entry.

**C2. Eager close.**
A Group's context is released when the last child that needed it completes.
Not at Group exit.

**C3. Context type inference.**
Atomic analyzes its subtree to pick the cheapest sufficient context:
only reads → Snapshot, any writes → Transaction, no needs → nothing opened.

---

## What follows from these rules

**From S1 + C3:**
Ungrouped Terms in a Flow automatically get optimal context.
No annotation needed. Zero cost when the substrate doesn't need it.

**From S4 + S1:**
Flow controls order. Group controls sharing. These compose freely.
`Atomic(Seq(...))` and `Seq(Atomic(...))` are both valid, mean different things.

**From B2 + B4:**
Context scoping is lexical. Innermost binding wins.

**From S2:**
Groups can be added or removed without changing computation.
They only affect resource sharing and consistency guarantees.
The computation topology (Terms + Flows) is Group-invariant.

Note: Group-invariance holds cleanly for pure computations.
For impure computations, Groups affect consistency guarantees
(e.g., whether two writes are atomic), which may affect
observable outcomes. The *intent* of the computation is
preserved; the *guarantees* change. See [formal.md](formal.md)
for a precise statement.
