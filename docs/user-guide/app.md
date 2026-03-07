# App

An App is a directory with a Shape, a flow, and optionally internal modules.

## Core Idea

**Shape = isolation boundary.** Shape defines an app in everybase. Every app owns its Shape. Flows read from it and write to it. Nothing leaks.

```text
my_app/
├── __init__.py    # re-exports
├── shapes.py      # Shape definitions
└── app.py         # flow entrypoints
```

Larger apps add internal modules alongside `app.py`:

```text
token_analytics/
├── __init__.py
├── shapes.py
├── poller.py      # block polling flow
├── enricher.py    # token enrichment flow
├── report.py      # reporting flow
└── app.py         # composes poller + enricher + report
```

## Shape-Centered Design

The Shape holds **all** state — inputs, intermediates, and outputs. Flows take the Shape type as their first argument and operate entirely through it.

```python
class TransferState(Shape):
    # Inputs (seed before running)
    wallet = KeypairRef.slot()
    recipient = PubkeyRef.slot()
    amount = LamportRef.slot()

    # Intermediate / output
    spec = TransactionSpecRef.slot()
    signature = ebv.StrRef.slot()
    status = ebv.StrRef.slot()
```

### Flows take Shape, not primitives

The flow's first argument is always `s: type[MyShape]`. Never scatter Python primitives as function parameters — put them in the Shape.

```python
# Wrong: scattered primitives, optional shape
def transfer(
    from_privkey: str,
    to_pubkey: str,
    amount_sol: float,
    *,
    s: type[TransferState] = TransferState,
) -> Flow:
    ...

# Right: shape-centered, caller seeds inputs
def transfer(
    s: type[TransferState],
    *,
    max_attempts: int = 3,
) -> Flow:
    ...
```

The only keyword arguments a flow should accept are **tuning parameters** (timeouts, retry counts, intervals) — things that configure behavior, not data.

### Callers seed the Shape

The caller (CLI, parent app, test) seeds the Shape inputs before running the flow:

```python
s = TransferState
flow = f.Seq(
    s.wallet.set(from_privkey),
    s.recipient.set(to_pubkey),
    s.amount.set_sol(amount_sol),
    transfer(s),
)
```

This is a flow tree — seeding happens at execution time, not at build time.

### Validate inputs, clear outputs

Flows should be robust: assert inputs exist, clear stale output state.

```python
def transfer(s: type[TransferState], *, max_attempts: int = 3) -> Flow:
    return f.Seq(
        # validate inputs
        f.AssertExists(s.wallet, "wallet not set"),
        f.AssertExists(s.recipient, "recipient not set"),
        f.AssertExists(s.amount, "amount not set"),
        f.Assert(s.amount > 0, "amount must be positive"),
        # clear stale output
        f.SkipIfMissing(s.signature, s.signature.remove()),
        f.SkipIfMissing(s.status, s.status.remove()),
        # do work
        s.spec.set(build_spec_term),
        send_transaction(s.spec.get(), signature_ref=s.signature, status_ref=s.status),
        f.Print("done — status:", s.status),
    )
```

## Composability via Shape Parameter

Because flows take `s: type[MyShape]`, they compose naturally. A parent app can embed a child app's Shape and pass it down:

```python
class ParentState(Shape):
    transfer = ebv.ShapeRef.slot(TransferState)
    other_data = ebv.IntRef.slot()

# Parent seeds child shape, then runs child flow
f.Seq(
    ParentState.transfer.wallet.set(kp),
    ParentState.transfer.recipient.set(dest),
    ParentState.transfer.amount.set_sol(1.0),
    transfer(ParentState.transfer),
)
```

The child flow doesn't know or care about nesting depth. It operates on whatever Shape ref it receives.

## Apps Import From Apps

There's no "reusable component" vs "specific app" distinction. All apps live in the same directory. Reusability is emergent — if one app needs another's flow, it imports it.

```python
# pumpfun_trade/app.py imports from send/
from my_project.apps.send import send_transaction

def pumpfun_buy(s: type[BuyState]) -> Flow:
    return f.Seq(
        s.spec.set(build_buy_spec_term),
        send_transaction(s.spec.get(), signature_ref=s.signature, status_ref=s.status),
    )
```

## Naming

Name apps specifically — what they do, not what category they belong to.

- `transfer` — transfers SOL
- `nonce_pool` — manages nonce accounts
- `pumpfun_trade` — buys/sells on PumpFun
- `token_analytics` — analyzes PumpFun tokens

Avoid generic names like `blocks` or `sync` unless the app is truly generic.

## Type Refs Conversion

Domain-specific refs (like `KeypairRef`, `LamportRef`) handle type conversion in their `set` method. Callers don't need to manually convert:

```python
# KeypairRef.set() accepts Keypair objects, base58 strings, or KeypairValue terms
s.wallet.set(from_privkey)           # string — stored as-is
s.wallet.set(keypair_object)         # Keypair — converted to base58

# LamportRef has set_sol() for SOL → lamports conversion
s.amount.set_sol(1.5)               # 1.5 SOL → 1_500_000_000 lamports
s.amount.set(500_000_000)           # raw lamports
```

Don't wrap values in `KeypairValue.from_base58()` or do manual `int(sol * 1e9)` — let the ref handle it.

## Summary

| Principle | Rule |
|-----------|------|
| **Shape = boundary** | Every app owns its Shape |
| **Flows take Shape** | First arg is `s: type[MyShape]`, never scattered primitives |
| **Callers seed** | Inputs are set in the flow tree before calling the flow |
| **Validate + clear** | Assert inputs exist, clear stale outputs |
| **Refs convert** | Type refs handle conversion — don't manually convert |
| **Flat hierarchy** | All apps in one directory, import freely |
| **Name specifically** | What it does, not what category |
