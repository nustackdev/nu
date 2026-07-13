---
title: Apps — principles for building on Nu
---

A Nu app is one tree that a runner evaluates. Every construct maps to a documented kind: Ref, Query, Command, Action, Flow, Span. This guide is the compressed source of truth — every bullet is one rule, an example only when it earns its place. Anti-patterns at the end are the failure modes a first attempt keeps landing on.

## Model foundation

- **The program must WRITE.** The root subtree must contain at least one Command / Action; a pure-Query composition is non-observable, its yield has no consumer, and the runner rejects it (`program_mutates` law).
- **Refs are the only Context seam.** Every READ and WRITE happens at a Ref. No Refs in a subtree, no effects in it. Extend Nu by shipping a Ref (Fabric + capabilities), never by hiding storage in a Query.
- **Writes → Command (mutates, no yield). Reads → Query (yields, no mutation).** Value-and-mutate in one atomic step (mint id and return, `pop`, `swap`, `INSERT ... RETURNING`) is a **ScalarAction** — one atom, atomic mutate-plus-yield. Modelling those as `Command >> Query` loses atomicity.
- **A Command's mutation slot must hold a Ref** (`ref_slots` law). Storing into a non-Ref voids the WRITE.
- **No held ctx on the public surface.** No `open_x(path) -> handle`, no `Logger(stream)`. Every interaction lives inside `nu.With(preset(...), body=...)`. The Ref addresses the location; the Bracket binds the Fabric.
- **Rows are `dict`.** Reads yield `list[dict]` produced by `DictForm.of(...)` inside the tree. Never wrap in a dataclass — the tree already produces the shape.

## The shape of an app

- One tree per app. Shapes at the top of the module, sub-trees composed with `>>` / `|` / `&`, one `nu.With(...)` at the bottom, `nu.run(tree)` (sync) or `asyncio.run(nu.arun(tree))` (async).
- App-shaped factories return **raw trees, unwrapped**. No `auto_flow_atomic` inside the factory. The deployer wraps once — it knows which shapes bind to which Navigators.
- Wrap in a `build_tree`, not at construction. Wrapping = per-scope `auto_flow_atomic` + default pass. Order matters (see [Atomicity](#atomicity-scope-retry-wrapping)).
- Call-site aliases at module top: `import nu` and use `nu.v` / `nu.m` — never `nu.virtuals` / `nu.mem`. For the UI fabric, prefer `nu.ui.X` at call sites (`nu.nd` is retained as a backward-compat alias only).

## Presets stack

- Every runtime dependency is a bracket. Stack them in one `nu.With(...)` head with `body=` last. Later brackets nest inside earlier ones and see their bindings.
- `nu.v.presets.rocksdb_navigator_inmemory(path)` provides Codec + Observer + Storage + Navigator in one drop-in. `nu.ui.presets.server(ui, port=)` boots a nudle UI actor. `nu.ray.presets.cluster(...)` boots Ray. Each returns a `With(...)` / `Provide(...)`.
- Ship your own preset as a factory returning `With(...)` / `Provide(...)`. Users drop it in the same head, no glue.
- Bracket **order matters**: a RO-secondary provider must land AFTER the primary it mirrors; the UI bracket opens LAST so the shard primaries it reads already exist.
- Distributed: fabric providers get `tag=Shape` (or `tags=(Shape, shard_id)`) plus `predicate=` for shard routing. `nu.invisibles.InvisiblesProxy(nu.v.fabrics.Navigator, address=..., tag=S)` fans one primary to many workers. `nu.ProvideDict(nu.ray.RayService, {k: cfg, ...}, parallel=True)` parametrizes a service across `k`.

## Chaining: use the Python DSL

- Nu Refs and Forms overload the Python operators. **Write Python; you get Nu.** `a > b` builds `GtQuery(a, b)`; `x["foo"]` builds `GetItemQuery(x, "foo")`; `x.field` builds `GetAttrQuery(x, "field")`; `a + b` / `a - b` / `a * b` / `a / b` build the arithmetic atoms.
  ```
  nu.WhileDo(w.cursor <= slot_to, walk_body)            # not LeQuery(w.cursor, slot_to)
  ledger_shard.blocks[w.cursor].txs[sc.current_tx_pos]  # not nested GetItemQuery(...)
  meta.slots_processed.store(meta.slots_processed + 1)  # not AddQuery(meta.slots_processed, 1)
  s.mints.missing()                                     # not nu.MissingQuery(s.mints)
  ```
- Reach for the raw atom name (`nu.GeQuery`, `GetItemQuery`, `GetAttrQuery`, `AddQuery`, ...) **only** when the DSL doesn't cover the case — a dynamic op picked at runtime, a factory building a query tree from data. Almost never at call sites.
- Comparisons: dunders for the ordering ops (`__lt__`, `__gt__`, `__ge__`, `__le__`); named methods for equality (`.eq()`, `.ne()`) so `__eq__`/`__hash__` stay Python-hashable.
- Boolean combinators are named: `.and_()`, `.or_()`, `.not_()`. `and`/`or`/`not` short-circuit at Python level and won't build a Nu tree.
- Ref navigation stacks: `LedgerShard.blocks[w.cursor].txs[i].signature` — every `[k]` and `.field` builds a sub-Ref; the whole chain resolves at eval time. See `legolas.apps.token_indexer.app` for dense chained navigation over a shard.

## Storage shape

- Reach for `nu.v.Kh57ShapesRef[T]` when the map wants indexed range walks or reservoir sampling (`entries.range(lo, hi)`, `entries.sample(n, lo, hi)`) — time-series, ordered scans. Str-key `ShapesDictRef` when order doesn't matter (registries, namespaces).
- Kh57 keys are 57 bits. When encoding a timestamp, offset from a recent epoch and shift for a sub-us counter so same-instant writes don't collide (`((us_since_2020) << 8) | (counter & 0xff)`).

## Capture once, derive

- Two `@nu.host(deterministic=False)` calls at different tree positions fire at different moments. If two slots need the SAME eval-time value (e.g. a key and its own timestamp leaf), minting each independently silently drifts them.
- Rule: capture into one `AttrRef` via `SetCommand`; derive every dependent slot by reading that attr.
  ```
  nu.SetCommand(us_attr, NowUs())                     # capture eval-time us
  >> nu.SetCommand(key_attr, EncodeKey(us_attr))      # derive from same us
  >> shape[key_attr].store(nu.DictForm.of(ts_us=us_attr, ...))
  ```
- `SetCommand(attr, <query>)` is a Command WRITE-ing `ctx.attrs`, so it composes with `>>` alongside other Commands. The attr Ref, re-read downstream, self-yields the captured value.

## Fresh eval-time state, parallel-safe

- Two channels for scratch:
  - **Loop-var side-channel** — `ForEachDo(items, body, item="tx")` + `nu.AnyAttrRef("tx")`; the atom binds each element into `ctx.attrs`, body reads via a typed AttrRef. Same story for `MapQuery(pairs, transform, key="_it")` / `FilterQuery(pairs, predicate, key="_it")`. The sanctioned surface for per-item state.
  - **Explicit `SetCommand(attr, <query>)`** — for eval-time captures no iterator binds (clock reads, id mint, derivation chains).
- Reserve loop-var and scratch-attr slot names so parallel branches never collide. Fixed names for fixed loops (`item="tx"`); a per-module `itertools.count()` for anonymous scratch (`nu.IntAttrRef(f"_ns_key_{next(_c)}")`).
- A stored `AttrRef` inside a Ref's dynamic key slot resolves at eval time: `shape.entries[key_attr]` reads `ctx.attrs[key_attr]` and addresses through it. So the whole write is `SetCommand(...) >> shape[key_attr].store(...)`.
- Worker-durable scratch (a slot cursor, a queue payload, a running counter) lives on a **mem Ref** (`w.cursor.store(...)`), NOT in `ctx.attrs`. Mem outlives an eval boundary; attrs don't. Attrs are for values that must not leak past a Command chain.
- Nothing on `self` (Terms are immutable, shared across runs). Nothing at construct time that must be fresh at eval time. Global counters at module scope are the right level for construct-time unique names.

## `@nu.host`, not a custom `ScalarQuery`

- Every eval-time Python bit (clock reads, encode / decode, formatting, id mint, hash) is a `@nu.host` function turned into a value-only atom by the factory. Declare `deterministic=False` on clocks and mints so the engine never folds them.
- A `@nu.host` atom is pure at the algebra boundary: children resolve first, then the callable runs on their values. No ctx, no state, no side-effects beyond returning the value. IO, storage, Context reads live in Refs and standard atoms.
- Custom `ScalarQuery` subclass reaching `rt.ctx` and running a nested `nu.run(...)` inside `_compile` IS the anti-pattern the model closes. It lets imperative Python run in a value slot invisibly to the effect algebra. Whatever you were about to write is expressible as either a Nu Query tree (for reads) or a ScalarAction (for atomic mutate-plus-yield). Write that.

## Reads are Nu trees; rows are dicts

- Shape of every read:
  ```
  nu.v.Snapshot(
      nu.CollectQuery(
          nu.MapQuery(
              nu.FilterQuery(nu.IterQuery(pairs), predicate, key="_it"),
              transform=nu.DictForm.of(id=..., ts=..., ...),
              key="_it",
          )
      ),
      scope=S,
  )
  ```
- `IterQuery` opens a scalar list into a stream. `MapQuery` / `FilterQuery` bind each item to a loop-var attr (`key="_it"`). The predicate / transform read the binding via `nu.AnyAttrRef("_it")` plus `_it[0]` / `_it[1]` to project key / view of a `(key, view)` pair.
- A scalar consumer refuses a stream child (`scalar_stream_refused` law). Reduction is the bridge: `CollectQuery` (drain), `FirstQuery`, `CountQuery`, `LenQuery` all take a stream and yield one value.
- Aggregate via `CountQuery(FilterQuery(...))` × N inside one `DictForm.of`: one Snapshot, N walks, tally comes back as a dict.
- Range-scoped reads on kh57: `entries.range(lo_key, hi_key)` returns a scalar list of `(key, view)` pairs. Wrap with `IterQuery` before Map / Filter.
- A read dropped into an already-wrapped body needs no explicit Snapshot — the outer wrap covers it. Only add `Snapshot(..., scope=S)` at the top of a standalone read.

## Ref addressing: structural vs value slots

- A hierarchical Ref holds its parent at `children[0]`, marked `structural` — address structure, resolved but never value-read, contributing no effect.
- `Logs.streams[stream].entries[key_attr]` — `streams` and `entries` in the parent chain are structural; both `[]` slots are value slots. A Ref in a value slot yields at eval time (the dual role). Same address, two roles decided by slot.
- `Logs.streams[ViewState.stream]` — the outer key is itself a Ref. In a value slot, it self-yields the current selection at every eval. Nothing in Python closes over "the stream"; the tree names the location and re-reads each generation.
- A subscription source (`ref.on_change()`, `WidgetRef.changed()`) is structural: the handle opens on the address once, no per-fire Snapshot on the source.

## Composition (`>>`, `|`, `&`, Bracket)

- `>>` = Sequential Strategy Flow. Every direct child must mutate (`flow_body_is_mutator` law). A Query in the body has no consumer — its yield is dropped and validation refuses it.
- `|` = Parallel Strategy Flow. Children mutate independently, fire order is unspecified.
- `&` = Race Strategy Flow. First branch to finish wins.
- To sink a Query yield into a Flow chain, **store it**: `ref.store(<query>)` is a Command. That is the only path a value enters a `>>` chain — the store is the value's consumer.
- **`Snapshot(body)` and `Transaction(body)` are Bracket Spans — transparent to their body.** They forward the body's yield in the same shape and cardinality. `Snapshot(scalar_query)` still yields a scalar; wrapping in a Bracket does NOT demote a Query to a Command. To use a Query inside `>>`, store it (rule above).
- The Bracket picks the atomic region:
  - `Snapshot(A | B | C, scope=S)` — one snapshot generation on S; multi-store reads see a consistent view.
  - `Transaction(A, B, scope=S)` — one atomic write on S; either both A and B land, or neither.
- A Bracket without `scope=` covers every virtuals ref reachable in the subtree — crushes independent-shape concurrency. Always pass `scope=` on every hand-written Snapshot / Transaction; the auto-wrapper does it for you when it lifts unwrapped writes.

## Atomicity: scope, retry, wrapping

- **Per-scope Transactions, never a global one.** Every `nu.v.Transaction(...)` and `nu.v.Snapshot(...)` carries `scope=Shape`. The scope pins the Bracket to that shape's Navigator so writes to disjoint shapes stay independent (they can even live in different DBs).
- **Wrap hot-key writes in `nu.v.RetryOnConflict(Transaction(..., scope=S), max_attempts=N)`.** Any write that touches a shared marker (set membership, dict marker, counter, `__len__`) is a hot-key conflict candidate under N workers. Naked Transaction there deadlocks under contention.
- **Bracket kind is picked by effect, not by wrapper shape.** WRITE through any ref in scope → Transaction; only READ / RESOLVE → Snapshot; neither → no wrap. `auto_flow_atomic` reads `tracked_effects(child)` and dispatches.
- **The pipeline** (once, in `build_tree`, on the composed body tree before it goes into `nu.With(...)` as `body=`):
  ```
  tree = nu.m.inline_refs(tree)          # legacy no-op (see below)
  tree = nu.v.inline_refs(tree)          # legacy no-op (see below)
  tree = nu.m.inline_refs(tree)          # legacy no-op (see below)
  for scope in (ShardA, ShardB, MetaA, RootA, ...):
      tree = nu.v.auto_flow_atomic(tree, scope=scope)  # scoped passes first
  tree = nu.v.auto_flow_atomic(tree)     # default pass sweeps the rest
  tree = nu.inspect.set_logger_name(tree, "app.name")
  ```
- **Scoped passes go before the default pass**, or the default sweeps every remaining write into one shapeless Transaction and the scoped passes find nothing left. Only `auto_flow_atomic` is load-bearing in the pipeline above.
- **`nu.m.inline_refs` / `nu.v.inline_refs` are retired identity no-ops** — runtime path resolution superseded ref flattening (a `StructuredRef` walks the on-tree parent chain, so a static flattening pass is no longer needed). See the `nu/src/nu/{mem,virtuals}/tree/inline_refs.py` docstrings. Distributed feed runs (`citadel.feed.feed_cluster_run.build_tree`, `citadel.feed.feed_red_run.build_tree`) still call the three-pass sandwich for backward compat; new code can drop the `inline_refs` calls entirely and go straight to the scoped `auto_flow_atomic` loop.
- **Init shared containers in a driver-side seed step.** N workers racing on a first-insert marker write on an empty container hit `StorageLockTimeoutError`. Pre-create with `nu.IfDo(x.missing(), x.store({}))` under a `Transaction(scope=x_root)` before the parallel pool fans out.
- **A worker parks on a gate with `WhileDo + DelayedDo(Noop())`** — `nu.WhileDo(cond.not_(), nu.DelayedDo(POLL, nu.Noop()))`. A bare `Retry` on a missing cursor is wrong; Retry is for failed attempts, `WhileDo` is for scheduled polling.

## Retry & recovery

- `nu.Retry(body, max_attempts=N, delay=D, backoff=B, jitter=J, on_attempt_fail=nu.log(...))` — outer retry Span for external-facing failures (RPC drops, rate limits). Jitter is non-optional under N parallel workers.
- Wrap the failing IO in a `TryCatch`: `nu.Retry(nu.TryCatch(work, fallback, errors=DroppedSlotError), ...)`. `errors=` filters which exceptions the fallback catches; every other error propagates and the retry counts.
- The retry Span binds `error` / `attempt` into `ctx.attrs` for the hook: `on_attempt_fail=nu.log("retry", refs, "err=", nu.StrAttrRef("error"), "attempt=", nu.IntAttrRef("attempt"))`. `nu.inspect.annotate_retries(tree)` bolts a default log hook onto every unhooked Retry in the tree.
- `TryCatch(body, nu.Noop(), errors=E)` is "swallow explicitly" — say so with `nu.log(...)` in the catch branch, don't leave it silent.
- Never handle a tree-raised exception by wrapping `nu.run(...)` in a Python `try`. Errors surface as `ctx.attrs["error"]` on the Retry hook; abort from inside with `nu.raise_(ExcCls, <msg_tree>)`.

## Reactive UI

- Match the shape of `counter.py` / `wish_jar.py` in `nu/examples/nudle/`:
  ```
  seed >> hydrate >> (tick | on_change_A | on_change_B | ...)
  ```
- **`tick`** — `ForeverDo(Snapshot(<repaint>, scope=S) >> Delay(N))`. Repaint = one Snapshot over a Parallel fan-out of stores (`Table.store(...) | Stat.store(...) | ...`) — atomic UI update.
- **`on_change_X`** — `ReactForever(WidgetRef.changed(), Transaction(ViewState.X.store(WidgetRef), scope=View) >> Snapshot(<repaint>, scope=S))`. Mirror the browser pick into a server-side `ViewState` shape, then repaint.
- **`ViewState`** is a tiny `nu.Shape` with `StrRef` / `IntRef` slots. The tick reads it; the browser never round-trips per-tick.
- **Dynamic keys** resolve every generation: `Logs.streams[ViewState.stream].entries` addresses through the current `ViewState.stream` at each Snapshot fire.
- **Cell formatting** is `@nu.host` (`FmtTs`, `FmtFields`, `RowAsList`) composed into the row `DictForm.of` — never a Python `for` loop over pulled rows.

## Async coherence

- `nu.run(tree)` = sync path. `asyncio.run(nu.arun(tree))` = loop path.
- An atom that declares `requires_async` (nudle, most io, network fabrics) must run on the loop (`async_atom_needs_loop` law) — putting it in `nu.run` fails validation before evaluation.
- A sync-only atom on the loop is a warning (`sync_atom_on_loop`), never an error — it works, it blocks the loop.
- Reach for `nu.arun` whenever the tree touches nudle, io, or a network-backed Fabric.

## Granularity of decomposition

- **Inline is fine when the subtree is short and appears once.** Two lines of Nu composed with `>>` at the call site are clearer than a helper named `_do_thing`.
- **Extract a Python `def _fn(...) -> nu.Nu` only when the subtree earns it.** Earn it means: (a) it's used twice or more, (b) it takes more than a handful of slots to build and hides the outer flow, or (c) it parametrizes over a shape/scope you want to reuse across shards. `legolas.apps.token_indexer` extracts `_walk_slot`, `_wait_processed`, `_indexer_worker` because each is used from more than one call site or has a distinct name in the model.
- **Module-level `nu.Nu` constants beat helper fns for one-shot flows.** `bg = nu.v.Transaction(...) >> nu.ForeverDo(...)` at module top reads faster than `def build_bg(): return ...`. Reserve helper fns for parametrized subtrees.
- **Don't factor out one-line assemblies.** `nu.MapQuery(pairs, nu.DictForm.of(...), key="_it")` inline reads better than `_row = nu.DictForm.of(...); nu.MapQuery(pairs, _row, key="_it")` when `_row` is used once.
- **Don't split a Command chain across fns just to name it.** A `Sequential` of four `.store(...)` Commands doesn't need `def _write_all(): return a >> b >> c >> d`. The `>>` shows the sequence.
- **When in doubt: one `nu.With(...)` and one `body=` at module top; helpers only when a reader would be lost without a name.**

## Values out to Python

- **Inside an app, don't.** Surface a value with `nu.log(<ref>, <query>, ..., level="info", logger="app.name")` — a Command that writes a formatted line via the stderr fabric; composes with `>>`, takes Nu children directly, is retargetable by `nu.inspect.set_logger_name`. `nu.print(<query>)` is the stdout equivalent for scripts.
- **Test convention** (matches nu's own `tests/nu/virtuals/functional/conftest.py`): the harness holds a ctx.
  ```python
  @pytest.fixture
  def ctx():
      with nu.v.presets.rocksdb_storage_inmemory(scratch) as storage:
          yield nu.Context().bind(Navigator, Navigator(storage))
  ```
  Tests write `nu.run(nu.v.Transaction(cmd, scope=S), ctx)` and read `nu.run(nu.v.Snapshot(atom, scope=S), ctx)[0]`. The held ctx never leaks past the fixture.
- `nu.run` / `nu.arun` return `(value, ctx)`. Element `[0]` is the yield.

## Anti-patterns

- `open_logs(path)`, `Logger(stream)`, `Store(path).new` — any Python object that holds a bound ctx and exposes `.method(...)` on it. All interaction goes through `nu.With(...)`.
- Custom `ScalarQuery` subclass reaching `rt.ctx` inside `_compile` to run a nested `nu.run(...)`. The "call back into Python with the store" escape hatch the model closes. `@nu.host` for pure values, Nu Query trees for reads, ScalarAction for atomic mutate-plus-yield.
- Snapshot-wrapping a Query and passing it into a Flow body slot. Snapshot is transparent; the body still yields; the Flow rejects it. Store the query into a Ref instead.
- Command with a non-Ref mutation slot. `Store(non_ref, value)` voids (`ref_slots` law).
- Python `for row in read(...):` at the caller driving further writes. Compose the loop as `ForEachDo(read_atom, body_atom, item="_row")`.
- Dataclass-wrapping a read's yield. `DictForm.of` inside the tree IS the row shape.
- `nu.v.Transaction(...)` with no `scope=` in an app. It means "lock every virtuals ref I could reach" and serializes independent shapes.
- A naked `Transaction` around a hot-key write (`slots_synced.add(slot)`, `token_count.store(token_count + 1)`) under N workers. Wrap in `RetryOnConflict` or the first conflict aborts the whole outer flow.
- Applying `auto_flow_atomic` inside an `App`-shaped factory. The deployer wraps once, per its scope registry; a pre-wrapped factory forces the caller to unwrap or double-wrap.
- Running the default `auto_flow_atomic` before scoped passes. The default sweeps everything into one bracket and the scoped passes find nothing left.
- Polling a gate with `nu.Retry(body, max_attempts=inf)`. Retry is for failed attempts; use `WhileDo(cond, DelayedDo(interval, Noop()))`.
- Reaching for `nu.GeQuery(a, b)` / `GetItemQuery(x, "foo")` / `GetAttrQuery(x, "field")` where `a > b` / `x["foo"]` / `x.field` builds the same tree.
- Boolean `and`/`or`/`not` on Nu terms — they short-circuit in Python and return the last Python operand, not a Nu tree. Use `.and_()` / `.or_()` / `.not_()`.
- Building at construct time what needs to be fresh at run time. `ts_ms = int(time.time() * 1000)` at import, then `.store(ts_ms)`, bakes a stale constant into `ForeverDo` loops.
- State on `self` in a custom atom. Terms are immutable and shared across runs; per-eval state lives in the `compile` thunk's closure.
- Aliasing `nu.virtuals as nv` / `nu.ui as nudle` / `nu.mem as m`. Use `nu.v` / `nu.ui` / `nu.m` at call sites, always.
- Splitting one write into "mint the id in Python, pass it as a kwarg to `entry(...)`, `entry` builds a Command that stores it." The id must be minted at eval time inside the tree — construct-time mint reuses one id per every eval of the same Command.
- Pre-formatting a typed value before `.store()`. A Ref knows its type via `_lift` / `_lower`; `.store()` takes the typed input. `str(dt)` before `.store()` skips the value boundary.
- Extracting every sub-expression into a helper `def`. Small inline reads faster than named fragments; helpers are for reuse and parametrization, not decoration.

## Reference apps

- `nulog` (`nustackdev/nulog`) — smallest end-to-end: `shapes` / `writes` / `reads` / `viewer`, five files. Every principle above lives here.
- `nu/examples/nudle/counter.py`, `wish_jar.py`, `kh57_stream.py` — the UI patterns the reactive section formalizes.
