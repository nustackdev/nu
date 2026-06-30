# Authoring Spans and Flows

Higher-order atoms that compose a body (Span) or several mutators (Flow). The
leaf-atom contract is in `core/AUTHORING.md` - read it first. This is the delta:
the patterns and gotchas specific to atoms whose children are other
interactions, not data.

## The thunk model, applied to bodies

Same contract as core: `compile(nid, children)` / `acompile` return a thunk that
closes over the **child thunks**. Here a child thunk *is a body* - calling it
runs that whole subtree.

- void/scalar body: `body(rt)` runs it; the value (or `None`) is the result.
- stream body: `body(rt)` returns an iterator; drive it with `sync_iter` /
  `aiter_any` from `core/_stream.py`.
- Always implement both `compile` and `acompile`. `emit` compiles **both eagerly**
  for every node, so an async-only atom must not raise in `compile` - return a
  thunk that raises when called (sync entry refuses async-only trees first).

## Structure in the tree, not payload

The hard rule that shapes these atoms. **Anything Nu-computable is a child;
`payload` is for opaque pure-Python config only.**

- **Optional branches are a `Noop` slot, not a recorded index.** Fix the slots,
  fill an absent one with `core.Noop()`, and read presence off the tree:
  `None if isinstance(self.children[i], Noop) else children[i]`. No
  `catch_slot` / `has_else` bookkeeping in payload. (`TryCatch` slots:
  `[body, catch, finally_, error_key]`.)
- **Names / keys are string-yielding children (`StrArg`), not strings in
  payload.** `Nu.__init__` auto-wraps a bare `"error"` into a `LiteralQuery`, so
  a default reads naturally and a caller can pass any `Nu[str]`. Execute it in
  the thunk to get the name.
- **Only genuinely non-Nu config stays in payload.** `TryCatch.errors` is a
  tuple of exception *classes* - not meaningful as a Nu - so it lives in
  `payload["errors"]`. That is the bar: if it could be a Ref/Query, it is a
  child.

## Type the child slots by their role

Constructor params take child Nus - type them by what the slot accepts, not
`object`. Use the kind union that names the role:

- **Returning slot** (the child yields a value): `Ref | Query | Action | Span`.
- **Non-returning slot** (effect only, yield discarded): `Flow | Command | Span`.
- **Generic slot** (genuinely any body): `Nu`. Use this when the slot is
  cross-cutting - a Span's body, or a branch whose shape must match a generic
  body. `TryCatch(body: Nu, catch: Nu | None, finally_: Flow | Command | Span | None)`:
  body and catch are generic (catch mirrors whatever body yields), finally_ is
  non-returning.

A bare value (key, name) is a `*Arg` alias (`StrArg`, `IntArg`, ...), which
already admits `str | Nu[str] | Sentinel`. The compiled-thunk params in the
helpers stay `Callable`, and a thunk's yield stays `-> object` (a Nu yields any
Python value) - role typing is for the Nu children, not the runtime values.

`Nu` is generic over its yield type (`Term[Runtime, V_co]`, `Nu[V]`) and the
`*Arg` aliases use it, but concrete atoms do not yet bind `V`, so a transparent
atom cannot statically forward its body's type. Annotate with unparameterized
`Nu` until the generic-propagation pass lands (a hierarchy-wide typing sweep,
backlog).

## attrs is the one inter-Nu channel

Bodies talk to each other through `ctx.attrs`, never a private side channel. A
handler that needs a value from its owner reads it at a known key; the owner
writes it there. `TryCatch` writes the exception with
`rt.ctx.attrs[error_key(rt)] = str(exc)` and the `catch` body reads it back via
`AttrRef(error_key)`. The author does not invent another mechanism.

## Span = transparent; resolve cardinality in-thunk

A Span declares `Cardinality.TRANSPARENT` and forwards its body's shape (slot 0).
`compile` has no `program`, so the resolved shape is read **in the thunk**:

```python
if rt.program.attrs[Attr.CHILD_CARDINALITY][nid] is Cardinality.STREAM:
    return _guard(rt, body, ...)   # stream: wrap iteration in a generator
return body(rt)                    # void/scalar: direct call
```

Laws (`lang/laws/spans.py`): a Span needs a body (slot 0), and its
`child_cardinality` must equal the body's - both hold automatically when body is
slot 0. Aux children (catch, finally, key) sit at later slots, unconstrained.

The semantics are in the model (Go: `model/04-attributes/04-cardinality.md`
"Choosing an atom's cardinality", `model/02-atoms/06-span.md` "Atomic
re-evaluation"). A span that re-runs or rolls back its body (Retry, Transaction)
evaluates the body fresh per attempt, realizing a stream body *inside* the
attempt - never resuming a half-drained stream.

## Handler isolation (ctx copy) vs persistence

Two disciplines:

- A handler whose side effects must **not** leak runs against a copy:
  `saved = rt.ctx; rt.ctx = saved._copy(); try: ...; finally: rt.ctx = saved`.
  Only its return value forwards. (`TryCatch.catch`.)
- A branch that must **persist** runs against the live `rt.ctx`. (`finally_`.)

Swapping `rt.ctx` is safe within a sequential subtree (restored before the thunk
returns). A swap visible to a concurrent parallel sibling sharing the runtime is
the one edge - bodies under a Policy are sequential, so it does not arise;
document it where it could.

## Flows: compose on the runtime, don't hand-roll

A Flow is `VOID` and owns no effects; its body slots carry the writes
(`flow_body_is_mutator` law). Two sub-shapes:

- **Strategy** composes mutators directly. Concurrency is the runtime's job:
  hand the child nids (`rt.program.children[nid]`) to the runtime primitive -
  `eval_parallel` / `aeval_parallel` (join), `aeval_race` (first done),
  `aeval_any` (first success). Never build a thread pool or `gather` in an atom.
  Per-child sync/async placement is resolved off `Attr.ON_LOOP` inside the
  runtime. `Race` / `AnyN` are async-only (`requires_async = Declared(value=True)`);
  their sync thunks raise as a backstop.
- **Control** runs bodies under Query params (a condition, an iterable). Declare
  `param_slots = Declared(value=frozenset({...}))`; the rest are body slots.
  Loop vars ride the attrs side-channel (`rt.ctx.attrs[name] = elem`), the same
  designated channel `Map` / `Filter` use.

Composition operators are sugar on the `Nu` base: `a >> b` -> `Sequential`,
`a | b` -> `Parallel`, `a & b` -> `Race`.

## Hot path: no trivial indirection

Atom thunks are the hot path. Inline one-line helpers (`errors is None or
isinstance(...)` goes inline, not a `_matched()` call). Keep a module-level
helper only when it is genuine shared logic with multiple callers - `_run_catch`
(ctx-swap, used by the scalar thunk and the stream guard) earns its place; a
one-liner does not.

## Specialize the thunk at compile, not per call

`compile` runs **once per program build**; the thunk it returns runs **per
execution**. So resolve every structural decision in `compile` and return the
thunk that already fits - the runtime should branch on data, never on shape.

- **An absent optional branch is decided once.** `_branches` resolves a `Noop`
  slot to `None` at compile, so the Noop never runs. Better still: build a
  different thunk per present/absent combination, so the runtime has *no*
  `if finally_ is not None` check at all. `TryCatch.compile` returns one of four
  thunks - pass-through (no catch, no finally - just `return body`), catch-only,
  finally-only, full - each with only the work it needs.
- **Collapse a no-op wrapper to its child.** When a wrapper adds nothing
  (`TryCatch(body)` with no handlers), `return body` - the child thunk *is* the
  behaviour, and the wrapper disappears from the hot path.
- **What you cannot specialize:** anything that needs the `program` (a
  synthesized attribute like `CHILD_CARDINALITY`). `compile` has no `program`,
  so a transparent atom still reads its body's cardinality per call. Keep that
  check; specialize everything around it.

## Async-only atoms and the loop

An atom that can only run on the event loop - it awaits an `asyncio` primitive
(`wait_for`, `sleep`, cancellation, a race) - declares
`requires_async = Declared(value=True)`. Then:

- its sync `compile` thunk is a **backstop that raises**; the sync entry
  (`run` / `first` / `collect`) refuses an async-only subtree first via
  `refuse_async_only`, so the raise is a safety net, not the path;
- `acompile` carries the real behaviour.

Strategy `Race` / `AnyN` are async-only; among spans, `Timeout` (and the rate
limiters) will be too.

## No per-run or cross-call state

A Term is immutable and shared across every execution of a compiled program (and
survives `with_children`). So:

- never stash per-run state on `self` - closure-capture it in the thunk or read
  it from `rt`;
- construction config that must survive `with_children` goes in `payload`
  (pure-Python only);
- state that must persist **across invocations** - a rate limiter's last-fire
  time, a debounce deadline - cannot live on the Term. Put it in `ctx.attrs`
  under a `StrArg` key (the one channel) or in runtime state. This is the
  constraint `Throttle` / `Debounce` must satisfy.

## Gotchas

- **No bare no-op `Command`.** The `command_has_write` law requires every
  Command to declare a mutation slot. A do-nothing placeholder is a childless
  `ScalarQuery` (that is what `core.Noop` is).
- **`compile` cannot see the program.** Read synthesized/inherited attributes in
  the thunk via `rt.program.attrs[Attr.X][nid]`; read child node ids via
  `rt.program.children[nid]`.
- **Writing through a Ref** takes the ref's own node id:
  `ref.write(rt, value, rt.program.children[nid][slot])` (see `context/ops.py`).
- **`Noop` is query-shaped.** It slot-fits where the matrix admits a ScalarQuery
  (value slots, Span aux slots). A universal no-op accepted in mutator/param
  slots would need the matrix to look through it like a Span - deferred.

## Tests

`tests/nu/spans/test_<sub>.py`, `tests/nu/flows/test_<sub>.py`. Cover: the
basis (sort/cardinality), each success/failure/propagate path, void + scalar +
stream bodies, sync and async (`run` / `arun`; stream roots via
`collect(compile(tree))`), and any isolation/persistence discipline. Async-only
flows: assert the sync entry raises.

Before finishing: `PYTHONPATH=src .venv/bin/python -m pytest tests/nu -q` green
and `.venv/bin/ruff check` clean. Project venv only, never bare `pytest` /
`ruff`.
