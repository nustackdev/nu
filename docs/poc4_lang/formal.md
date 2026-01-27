# Topology Language — Formal Semantics

## 1. Syntax

Inductive definition of the abstract syntax.

### Sorts

```
v ∈ Val                          values
l ∈ Loc                          locations
c ∈ CtxType                      context types
s ∈ Substrate                    substrate instances
op ∈ PureOp                      pure operations
cmd ∈ ImpureOp                   impure operations
```

### Terms (0-cells)

```
t  ::=  ref(l)                   reference to location
     |  lit(v)                   literal value
     |  op(t₁, ..., tₙ)         pure morphism (n ≥ 1)
     |  cmd(t₁, ..., tₙ)        impure morphism (n ≥ 1)
```

### Flows (1-cells)

```
f  ::=  seq(u₁, ..., uₙ)       sequential             (n ≥ 1)
     |  par(u₁, ..., uₙ)       parallel                (n ≥ 1)
     |  cond(t, u₁, u₂)        conditional
```

### Groups (2-cells)

```
g  ::=  grp(c, u₁, ..., uₙ)    grouped context         (n ≥ 1)
     |  root(S, u)              root group, S = {s₁, ..., sₘ}
```

### Units

```
u  ::=  t  |  f  |  g
```

---

## 2. Well-formedness

Judgment form: `⊢ u ok`

### Children constraint

```
                ⊢ tᵢ ok    (for all i)
    ──────────────────────────────────────
          ⊢ op(t₁, ..., tₙ) ok                 [WF-PureOp]


                ⊢ tᵢ ok    (for all i)
    ──────────────────────────────────────
          ⊢ cmd(t₁, ..., tₙ) ok                [WF-ImpureOp]


                ⊢ uᵢ ok    (for all i)
    ──────────────────────────────────────
          ⊢ seq(u₁, ..., uₙ) ok                [WF-Seq]


                ⊢ uᵢ ok    (for all i)
    ──────────────────────────────────────
          ⊢ par(u₁, ..., uₙ) ok                [WF-Par]


          ⊢ t ok    ⊢ u₁ ok    ⊢ u₂ ok
    ──────────────────────────────────────
          ⊢ cond(t, u₁, u₂) ok                 [WF-Cond]


                ⊢ uᵢ ok    (for all i)
    ──────────────────────────────────────
          ⊢ grp(c, u₁, ..., uₙ) ok             [WF-Grp]


                    ⊢ u ok
    ──────────────────────────────────────
          ⊢ root(S, u) ok                      [WF-Root]
```

Note: [WF-PureOp] and [WF-ImpureOp] require children to be Terms (not arbitrary Units).
[WF-Seq], [WF-Par], [WF-Grp] accept any Units. This encodes R1-R3.

---

## 3. Needs

The function `needs : Unit → P(CtxType)` collects context requirements.

```
    needs(ref(l))              =  ctx_type(l)
    needs(lit(v))              =  ∅
    needs(op(t₁,...,tₙ))      =  ⋃ᵢ needs(tᵢ)
    needs(cmd(t₁,...,tₙ))     =  ⋃ᵢ needs(tᵢ)
    needs(seq(u₁,...,uₙ))     =  ⋃ᵢ needs(uᵢ)
    needs(par(u₁,...,uₙ))     =  ⋃ᵢ needs(uᵢ)
    needs(cond(t, u₁, u₂))    =  needs(t) ∪ needs(u₁) ∪ needs(u₂)
    needs(grp(c, u₁,...,uₙ))  =  (⋃ᵢ needs(uᵢ)) \ {c' | c' <: c}
    needs(root(S, u))         =  ∅     (root must satisfy all)
```

A Group **absorbs** needs it provides. Needs not absorbed propagate up.

---

## 4. Context Map

```
    Σ : CtxType ⇀ Ctx            partial function (context map)
```

Where `Ctx` is the set of context instances. Each context instance
has type `type(ctx) ∈ CtxType`.

Substrate map (available factories):

```
    Φ : CtxType → Substrate       maps context types to factories
```

---

## 5. Operational Semantics

Big-step evaluation. Judgment form:

```
    Σ; Φ ⊢ u ⇓ v ; Σ'
```

Read: "Under context map Σ and substrate map Φ, unit u evaluates
to value v, producing updated context map Σ'."

### Term evaluation

```
          Σ(ctx_type(l)) = ctx    ctx.get(l) = v
    ────────────────────────────────────────────────
              Σ; Φ ⊢ ref(l) ⇓ v ; Σ                  [E-Ref]


    ────────────────────────────────────────────────
              Σ; Φ ⊢ lit(v) ⇓ v ; Σ                  [E-Lit]


          Σ; Φ ⊢ tᵢ ⇓ vᵢ ; Σ    (for all i)
              ⟦op⟧(v₁,...,vₙ) = v
    ────────────────────────────────────────────────
          Σ; Φ ⊢ op(t₁,...,tₙ) ⇓ v ; Σ              [E-PureOp]


          Σ₀ = Σ
          Σᵢ₋₁; Φ ⊢ tᵢ ⇓ vᵢ ; Σᵢ    (for i = 1..n)
              ⟦cmd⟧(v₁,...,vₙ; Σₙ) = (v, Σ')
    ────────────────────────────────────────────────
          Σ; Φ ⊢ cmd(t₁,...,tₙ) ⇓ v ; Σ'            [E-ImpureOp]
```

Note: [E-PureOp] does not thread Σ (no side effects).
[E-ImpureOp] threads Σ through children and the operation itself.

### Flow evaluation

```
          Σ₀ = Σ
          Σᵢ₋₁; Φ ⊢ uᵢ ⇓ vᵢ ; Σᵢ    (for i = 1..n)
    ────────────────────────────────────────────────
          Σ; Φ ⊢ seq(u₁,...,uₙ) ⇓ vₙ ; Σₙ           [E-Seq]


          Σ; Φ ⊢ uᵢ ⇓ vᵢ ; Σᵢ    (for all i, independently)
              Σ' = merge(Σ₁,...,Σₙ)
    ────────────────────────────────────────────────
          Σ; Φ ⊢ par(u₁,...,uₙ) ⇓ (v₁,...,vₙ) ; Σ'  [E-Par]


          Σ; Φ ⊢ t ⇓ v ; Σ₁
              v = true    Σ₁; Φ ⊢ u₁ ⇓ v' ; Σ'
    ────────────────────────────────────────────────
          Σ; Φ ⊢ cond(t, u₁, u₂) ⇓ v' ; Σ'          [E-Cond-T]


          Σ; Φ ⊢ t ⇓ v ; Σ₁
              v = false   Σ₁; Φ ⊢ u₂ ⇓ v' ; Σ'
    ────────────────────────────────────────────────
          Σ; Φ ⊢ cond(t, u₁, u₂) ⇓ v' ; Σ'          [E-Cond-F]
```

Note: [E-Par] evaluates children with the same input Σ (isolation).
`merge` is substrate-defined (e.g., conflict resolution for concurrent writes).

### Group evaluation

```
          c ∈ dom(Φ)
          ctx = Φ(c).create()
          Σ' = Σ[c ↦ ctx]
          Σ'; Φ ⊢ seq(u₁,...,uₙ) ⇓ v ; Σ''
          ctx.release()
    ────────────────────────────────────────────────
          Σ; Φ ⊢ grp(c, u₁,...,uₙ) ⇓ v ; Σ'' \ {c}  [E-Grp]


          Φ' = substrates_to_map(S)
          Σ; Φ' ⊢ u ⇓ v ; Σ'
          release_all(Φ')
    ────────────────────────────────────────────────
          Σ; Φ ⊢ root(S, u) ⇓ v ; Σ'                [E-Root]
```

Note: [E-Grp] extends Σ with a new context, evaluates children,
then removes it (scoped). The context is available to all children
via the extended Σ'.

---

## 6. Implicit Grouping

Define the desugaring function `ι`:

```
    ι(seq(u₁,...,uₙ))  =  seq(ι'(u₁),...,ι'(uₙ))
    ι(par(u₁,...,uₙ))  =  par(ι'(u₁),...,ι'(uₙ))
    ι(cond(t, u₁, u₂)) =  cond(t, ι'(u₁), ι'(u₂))
    ι(grp(c, u₁,...))   =  grp(c, ι(u₁),...)
    ι(root(S, u))       =  root(S, ι(u))
    ι(t)                =  t                 (Terms unchanged)
```

Where `ι'` wraps direct Term children of Flows:

```
    ι'(t) = atomic(t)           if t is a Term
    ι'(u) = ι(u)                otherwise
```

And `atomic(t)` is defined as:

```
    atomic(t) = grp(infer(t), t)

    infer(t)  = Transaction     if writes(t)
    infer(t)  = Snapshot        if reads(t) ∧ ¬writes(t)
    infer(t)  = ⊥               if ¬reads(t) ∧ ¬writes(t)     (no group needed)
```

Where `writes(t)` and `reads(t)` are static analyses over `needs(t)`.

**Axiom A1** is then: evaluation always applies ι first.

```
    eval(u) ≡ eval(ι(u))
```

---

## 7. Erasure and Group Invariance

Define erasure `ε` (strip all Groups):

```
    ε(t)                  =  t                              (Terms preserved)
    ε(seq(u₁,...,uₙ))    =  seq(ε(u₁),...,ε(uₙ))
    ε(par(u₁,...,uₙ))    =  par(ε(u₁),...,ε(uₙ))
    ε(cond(t, u₁, u₂))   =  cond(t, ε(u₁), ε(u₂))
    ε(grp(c, u₁,...,uₙ)) =  seq(ε(u₁),...,ε(uₙ))          (dissolve group)
    ε(root(S, u))         =  ε(u)                           (dissolve root)
```

### Theorem 1 (Group Invariance for Pure Computations)

Let `u` be a unit where every morphism is pure (no `cmd` nodes).
Let Σ be a context map where all reads are deterministic.

```
    If   Σ; Φ ⊢ u ⇓ v ; Σ'
    and  Σ; Φ ⊢ ε(u) ⇓ v'' ; Σ'''
    then v = v''
```

*Proof sketch.* By structural induction on u.
- Base case (Term): ε(t) = t, same evaluation.
- Flow case: ε preserves structure, induction on children.
- Group case: ε(grp(c, u₁,...)) = seq(ε(u₁),...). Group only adds/removes
  context in Σ. Pure operations (E-PureOp) do not read Σ for side effects,
  only for ref resolution. If all reads are deterministic (same value
  regardless of context sharing), the result is identical. ∎

### Theorem 1' (Group Invariance — Limitation)

For impure computations, Group invariance does **not** hold in general.
Counterexample: two concurrent writes under `par` may produce different
results depending on whether they share a Transaction (serialized)
or get independent contexts (concurrent).

Groups affect **consistency guarantees**, not pure computation.

---

## 8. Resolution

Define resolution as a function:

```
    resolve : Unit × CtxType × Tree → Ctx | ⊥
```

Given a unit u, a needed context type c, and the full tree for
ancestor traversal:

```
    resolve(u, c, tree) =
        let ancestors = path_to_root(u, tree)
        in  first(λ a. a = grp(c', ...) ∧ c <: c', ancestors)
            |> λ g. g.context(c)
            | None →
              first(λ a. a = root(S, ...) ∧ c ∈ dom(S), ancestors)
              |> λ r. r.substrate(c).create()
              | None → ⊥
```

### Theorem 2 (Resolution Determinism)

For a well-formed tree with a root group covering all needs:

```
    If   needs(u) ⊆ dom(Φ)     (root provides all substrates)
    then resolve(u, c, tree) ≠ ⊥    for all c ∈ needs(u)
```

*Proof.* By definition of `needs`: the root absorbs all needs (needs of
root = ∅). Every c ∈ needs(u) is either absorbed by an intermediate
Group (case 1 of resolve) or reaches the root's substrate map (case 2).
Since needs(u) ⊆ dom(Φ), resolution succeeds. ∎

---

## 9. Summary of Metatheory

| Property | Statement | Status |
|----------|-----------|--------|
| Well-formedness decidable | `⊢ u ok` is decidable | Immediate (syntax-directed) |
| Needs decidable | `needs(u)` is computable | Immediate (structural recursion) |
| Resolution deterministic | Theorem 2 | Proved |
| Group invariance (pure) | Theorem 1 | Proved (sketch) |
| Group invariance (impure) | Theorem 1' | Counterexample given |
| Desugaring preserves well-formedness | `⊢ u ok ⟹ ⊢ ι(u) ok` | By construction of ι |
