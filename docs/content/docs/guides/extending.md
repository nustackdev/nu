---
title: Extending Nu — stdlib, interactions, forms, fabrics
---

How to add to Nu: a new stdlib module, an interaction atom, a value-type Form, a fabric ref. Dense, atomic know-how — each bullet is one insight, not prose. Cull freely. Examples are illustrative, not copy-paste contracts.

## Layout & mirroring

- `nu.std` mirrors Python's stdlib 1-1: one submodule dir per module (`uuid/`, `datetime/`, `math/`, ...). Import like the stdlib: `from nu.std.uuid import UUID, uuid4`; `import nu.std.math as math`.
- 3-layer template per module: `forms.py` (the type as a Form/class), `functions.py` (module-level free functions), `interactions.py` (the atoms). `__init__.py` re-exports to mirror `import <mod>`.
- Omit layers a module doesn't need: value types (uuid, datetime, decimal, pathlib, cmath) skip `functions.py`; function modules (math, random, functools, itertools) skip `forms.py`; `datetime` has no free functions, `math` has no class.
- No shortcut re-export at `nu.std` top level — go through the submodule, like the real stdlib.
- Examples live in `examples/std_<mod>.py` (`eN = expr; print(run(eN)[0], type(eN), eN)`). Functional tests in `tests/nu/std/test_<mod>.py`, asserting against the real Python module, sync + at least one async (`arun`).

## Three ways to model an op (pick in this order)

- Reuse a core atom if it already expresses the op. Comparisons → `EqQuery`/`LtQuery`/...; arithmetic → `AddQuery`/`SubQuery`/... (Python does the real op on resolved values, so `date + timedelta` "just works"); attribute reads → `GetAttrQuery` (`.year`, `.real`, `.days`).
- `InteractionFactory` for "call a fixed Python callable" — constructors, free functions, methods. Non-hot paths only.
- Hand-write a `StreamQuery`/`Reduction` atom for hot-path stream/fold ops (itertools, functools) — no factory hop.

## Forms (the typed access surface)

- A type → a Form: `class UUID(Form, TypedNu[_pyUUID])`. The Form wraps a Nu child term; its methods return more terms.
- Name mirrors Python: lowercase `date`/`timedelta`/`complex` need `# noqa: N801`; already-capitalized `UUID`/`Decimal`/`Fraction` need nothing.
- `__init__` is reserved (TypedNu wraps the child), so the literal constructor is a classmethod `.of(...)`; alternate constructors are classmethods (`from_iso`, `from_str`, `today`, `now`). `date.of(2026, 6, 30)`.
- Module-level free functions (`uuid4`, `sqrt`) are NOT methods on the class — they live in `functions.py`. A wrapper function builds the atom and returns the Form: `def uuid4() -> UUID: return UUID(Uuid4Query())`.
- Form method = build interaction, wrap result: `def version(self) -> IntForm: return IntForm(GetAttrQuery(self, "version"))`.
- Operator dunders (`__add__`, `__gt__`, `__truediv__`) build core atoms and return the right Form.
- Comparisons: `__lt__/__gt__/__ge__/__le__` as dunders; `eq()/ne()` as named methods (don't override `__eq__`/`__hash__`).

## InteractionFactory (`nu.lang.factory`)

- `InteractionFactory(base_kind, name, fn, **attrs)` → a named `Nu` subclass that resolves its children then calls `fn(*args, **kwargs)`. `ScalarQueryFactory(name, fn)` is the kind-fixed helper (the common case).
- A method is just a callable: an *unbound* method takes the receiver first, so `d.weekday()` ≡ `date.weekday(d)`. Bind the unbound method: `Weekday = ScalarQueryFactory("Weekday", date.weekday)`, receiver is the first child.
- This is why the factory subsumes constructors, classmethods, free functions, and methods — they're all "call a callable on resolved children." There is no separate "method call" atom.
- The callable is captured in the class body (code), not passed as data — that's what keeps it out of the old opaque-`FuncCall` escape hatch. Only a method *name* (a string) or a fixed callable ever appears; never an opaque callable as a child/payload.
- Supports positional + keyword children, sentinel propagation, sync/async inference (`async def` → `requires_async`, async-only `acompile`), and declared attributes via `**attrs`.
- Rejects stream/reduction/flow/span kinds — those are hand-written.
- Factory atoms type-check as `type[base]`, so pyright can't see kwargs or a specific signature: for a kwarg call pyright rejects, bind a small lambda fixing the arg shape (`ScalarQueryFactory("X", lambda a, k: fn(a, k=k))`).

## Atom authoring (the deep rules)

- Core atoms are hand-written e2e (one clean `compile`/`acompile` thunk) for the hot path; the factory adds 1-2 hops, so it's for non-hot stdlib only. Streams/folds are hot → hand-written.
- Atoms are UNTYPED at the value level: `compile(self, nid, children) -> Callable`; thunks return `object`. Typing lives in Forms + `Arg` aliases, never on atoms.
- Implement `compile` and/or `acompile` for the modes the atom supports — most do both (the async twin mirrors the sync one with `await` on each child thunk). Async-only atoms implement just `acompile` and declare `requires_async = Declared(value=True)`; sync-only atoms implement just `compile`. The factory infers this from the callable (`async def` → async-only + `requires_async`).
- Children are precompiled thunks `(rt) -> value`. Call them to get values. Propagate sentinels before using: `v = child(rt); if v is EMPTY or v is INVALID: return INVALID`.
- Absence / "not provided" markers: reuse `UNSET` from `nu.lang.sentinels` (a Sentinel distinct from EMPTY/INVALID; it never propagates — callers test `is UNSET`). Don't mint ad-hoc `object()` sentinels.
- NO state on `self` — Terms are immutable and shared across runs. Per-run state lives in the `compile` thunk's closure, never on the instance (span/bracket lifecycle is a closure, not `self`).
- ALL arguments are children (resolved at runtime), NOT payload. Payload is for intrinsic constants only — a literal value, a static name (a method name, a loop-var key). Opaque, never traversed. Anything Nu-computable is a child.
- Pick the kind by behavior: yields one value → `ScalarQuery`; yields a stream → `StreamQuery`; folds a stream → `Reduction`; writes → `Command`; writes-and-yields → `ScalarAction`/`StreamAction`.
- Stream atoms: the thunk returns a generator. Iterate a child with `from nu.core._stream import sync_iter, aiter_any` (a sentinel child = empty stream). Sources build a generator; lenses pull+re-yield; folds (`Reduction`) drain to a scalar. Keep the async path LAZY — never `[x async for x in ...]`-collect a source you only partially consume, or an infinite source (count/cycle/repeat) hangs.
- Materialize a stream to a value with `CollectQuery(stream)` (drains to a list); a scalar `ListQuery` / `IteratorForm.to_list()` over a `StreamQuery` is refused by the cardinality laws.
- Higher-order op (a "function" argument): pass it as a Nu query CHILD plus a loop-var key; bind each item `rt.ctx.attrs[name] = elem`, then evaluate the child. The user's function reads the item via a typed AttrRef (`IntAttrRef("item")`). Folds bind two vars (`acc` + `item`). This is the sanctioned loop-var side-channel — NOT a tracked fabric write, so do NOT declare `mutates`.
- A `Reduction`'s source child must be a stream — wrap a raw iterable with `IterQuery` (`ReduceQuery(IterQuery(iterable), fn)`).
- Reuse Python's C-level implementation where you can: a pure combinator can `yield from itertools.<fn>(resolved...)` inside the generator — correct and fast. Hand-roll only the higher-order ones (the callable is a Nu term, not a Python fn).

## Attribution (Declared attributes)

- The kind sets `sort` + `cardinality` automatically; a factory/hand-written subclass inherits them. Pure ops declare nothing extra.
- Declare algebra where true: `commutative = Declared(value=True)`, `associative`, `idempotent`.
- Declare `mutates = Declared(value=frozenset({0}))` for a fabric write; the named slot holds the Ref, and effect synthesis binds it WRITE.
- `**attrs` on the factory covers all of these generically: a raw value is wrapped in `Declared`; a pre-built `Attribute` (incl. computed `Synthesized`/`Inherited`) passes through.
- Non-determinism (`uuid4`, `now`, `random.*`, `time`) declares `deterministic=False` (the algebra attribute). A fold/cache pass gates on pure AND deterministic, so these stay un-folded. Effects that produce no value but must not be dropped (`time.sleep`, `asyncio.sleep`) also carry `deterministic=False` as a conservative fold-guard until the io/effect model lands; `time.sleep` is sync-only (`async_affinity=False`), `asyncio.sleep` is async-only (an `async def`, so `requires_async=True`).

## Type-hinting gotchas

- `from __future__ import annotations` everywhere; lazy-import atoms/Forms INSIDE methods (avoids cycles; Forms reference each other).
- `Arg[T] = T | Nu[T] | Sentinel`; define `type XArg = Arg[_pytype]` under `TYPE_CHECKING` for params.
- `@overload` operands must NOT use the `Arg[T]` alias — it bundles `Sentinel`, so any two `Arg` overloads overlap (`reportOverlappingOverload`). Type overload operands as `FormClass | _pytype`; keep the full `Arg` union on the impl signature. (Needed when a return type depends on the operand, e.g. `date - date → timedelta` vs `date - timedelta → date`.)
- Passing an `object`-typed runtime value into a typed Python callable → `cast("T", value)` at the bridge (author-guaranteed, zero runtime cost). Quote the cast type string (ruff TC006).
- Reaching into `term.children[0]` returns `Term`, not `Nu` → `cast("Nu", ...)`.
- `run(term)` / `arun(term)` return `(value, ctx)`; the value is element `[0]`. Both work without an explicit ctx for pure terms.

## Fabrics & refs (the storage side)

- A fabric is an addressable space where Refs live; a Ref is per-fabric (no fabric-less Ref). The Ref owns read + write against its fabric, not core.
- Ref read = a `compile`/`acompile` thunk; write/erase = `write(rt, value, nid)` / `erase(rt, nid)`; addresses resolve along the parent-ref chain.
- Fabric interactions (store/erase) go THROUGH the ref and declare `mutates` on the slot holding it; the address is just another child (a Literal for a static key, any Nu for a computed one) — never a special payload.
- v2 substrate seam = `_StructuredRef`: address resolution + plug-points (`aresolve_address`, `afetch_parent`, `_wrap_*`, `coerce`, `write`/`erase`). A concrete fabric (mem, virtuals) supplies these; the navigation logic is shared.
- Group fabric code by domain, not by Nu kind: `interactions/item.py`, `interactions/collections.py`, `interactions/atomicity.py` — refs plus the interactions that touch them.

## Workflow

- Run `PYTHONPATH=src .venv/bin/python`; ruff `.venv/bin/ruff`; pyright `uvx pyright --pythonpath .venv/bin/python`. Never bare `pytest`/`ruff`.
- A new module is "done" when: example runs and matches the real Python module, ruff clean, pyright clean, functional tests green (sync + async — and async tests must finish, i.e. no infinite-source hang).
- Copy the closest existing module as the template: `datetime` (multi-class value type), `math` (function module), `itertools` (hand-written streams), `functools` (a `Reduction` fold).
