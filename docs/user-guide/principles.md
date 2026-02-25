# Principles

Core design principles for building everybase apps. These are non-negotiable.

## Terms over injection

Express logic as term trees, not injected Python functions.

```python
# Wrong: inject a function to do the work
result = FuncCallOp(extract_mint, tx)

# Right: compose terms that do the work
mint = ListValue(tx.token_balances.get()).pluck_("mint").filter_(bool).first()
```

`FuncCallOp` is an escape hatch, not a building block. Every time you reach for it, ask: can this be a term? If the answer is "not yet", consider adding the missing primitive.

## Primitives over helpers

When term algebra can't express something, add a primitive — don't normalize injection.

A 5-line helper behind `FuncCallOp` is acceptable as a temporary bridge. A pattern of helpers is a signal that primitives are missing. Fill the gap in the type system, then delete the helper.

```python
# Temporary: helper for cross-dict delta (no dict-join primitive yet)
token_delta = IntValue(FuncCallOp(_max_token_delta, pre_dict, post_dict))

# Future: once a primitive exists, replace
token_delta = pre_dict.delta_by_(post_dict).max_(key=lambda d: abs(d))
```

## Create Types for data, not functions

When you have domain-specific data with operations on it, create a Type — don't scatter Python functions. Types are the unit of domain knowledge.

```python
# Wrong: functions operating on raw dicts
def calculate_market_cap(curve_data):
    return curve_data["real_sol_reserves"] * TOTAL_SUPPLY / curve_data["real_token_reserves"]

market_cap = IntValue(FuncCallOp(calculate_market_cap, raw_data))

# Right: Type wraps data + exposes methods as term algebra
class BondingCurveType(TypeBase):
    def market_cap(self) -> IntValue:
        return IntValue(MethodCallOp(self, "market_cap_lamports"))

curve = BondingCurveValue(Services.pumpfun.get_bonding_curve(mint))
s.market_cap.set(curve.market_cap())  # term algebra, no FuncCallOp
```

**Rule of thumb**: if you have 3+ `FuncCallOp` helpers operating on the same data structure, that data structure wants to be a Type.

## Flow trees over Python control flow

Orchestration belongs in Flow trees, not in Python `if/for/while`.

```python
# Wrong: Python control flow inside a flow builder
def build_flow(items):
    steps = []
    for item in items:
        if item.needs_processing:
            steps.append(process(item))
    return f.Seq(*steps)

# Right: Flow primitives handle control
f.ForEach(items, f.If(item.needs_processing, process(item)))
```

Flow trees are inspectable, serializable, and composable. Python control flow is opaque.

## Design for continuity and resumability

Apps should be continuous (keep running), resumable (stop/start without loss), and recoverable (handle missed data).

### Shape as state machine

Encode progress in Shape slots so the app can resume from where it stopped.

```python
class SyncState(Shape):
    current_slot = pv.IntRef.slot()    # cursor: where we are now
    slots_synced = pv.ListRef.slot(int) # completed work
    completed = pv.BoolRef.slot()      # done flag

# In flow: skip already-processed work
f.If(
    s.slots_synced.contains(s.current_slot).not_(),
    process_slot,
)
```

### Fault tolerance via flow composition

```python
# Wrap risky operations in TryCatch + Retry
f.ForRange(0, n_slots,
    f.TryCatch(
        f.Retry(
            fetch_and_process_block,
            max_attempts=3,
            delay=0.5,
            backoff=2.0,
        ),
        catch=f.Seq(
            f.Print("failed, skipping slot", s.current_slot),
            s.current_slot.set(s.current_slot + 1),
        ),
    ),
)
```

## Components do one job

Each component (flow-building function) should have a single responsibility. Compose components at the app level.

```python
# Good: separate concerns
def block_poller(s, n_slots, tx_filter) -> Flow:
    """Fetch blocks, filter txs, route to shapes."""
    ...

def token_enricher(s) -> Flow:
    """Fetch bonding curves, compute metrics."""
    ...

# App composes components
def token_analytics(n_slots: int) -> Flow:
    return f.Seq(
        block_poller(s, n_slots=n_slots, tx_filter=filter),
        token_enricher(s),
        f.Print(report),
    )
```

## Parallel and Reactive for live systems

For continuous, live systems use `Race` to run producers and consumers concurrently, and `ReactWhile`/`ReactForever` to trigger processing on data changes.

```python
# Producer-consumer pattern
f.Race(
    # Producer: poll for new blocks
    f.Forever(f.Seq(
        s.current_slot.set(Services.solana.get_slot()),
        fetch_block_and_store(s),
        f.Delay(poll_interval),
    )),

    # Consumer: react to new data, run enrichment
    f.ReactForever(
        s.tokens.on_children_change(),
        enrich_token(s),
    ),
)
```

**Key insight**: pollers push data into shapes; reactive flows trigger on shape changes and process downstream. This decouples ingestion from computation.

## Service terms are lazy

Service calls (e.g., `Services.solana.get_slot()`) return term nodes, not results. They compose without evaluation and resolve only at execution.

```python
# This doesn't call the RPC — it builds a term tree
slot = Services.solana.get_slot()
block = Services.solana.get_block(slot)  # slot is still a term

# The tree evaluates when the flow executes
s.current_block.set(block)  # RPC calls happen here
```

This means you can build entire flow trees in a regular Python function without any async/await. The flow engine handles execution.
